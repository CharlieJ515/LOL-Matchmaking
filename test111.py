import argparse
from typing import List

import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchmetrics
from torch.utils.data import TensorDataset, DataLoader

from sqlalchemy import create_engine
import pytorch_lightning as pl
from pytorch_lightning.loggers import MLFlowLogger

EXCLUDED_COLS: List[str] = [
    "match_id", "participant_id", "team_id", "puuid",
    "champion_id", "champion_name",
    "item0", "item1", "item2", "item3", "item4", "item5", "item6"
]


class LoLPlayerDataModule(pl.LightningDataModule):
    def __init__(
        self,
        db_url: str,
        train_query: str,
        val_query: str,
        batch_size: int = 256,
    ):
        super().__init__()
        self.db_url = db_url
        self.train_query = train_query
        self.val_query = val_query
        self.batch_size = batch_size

    def prepare_data(self):
        engine = create_engine(self.db_url)

        self.train_df = pd.read_sql(self.train_query, engine)
        self.val_df = pd.read_sql(self.val_query, engine)

        self.train_df.drop(columns=[c for c in EXCLUDED_COLS if c in self.train_df.columns],
                           inplace=True, errors="ignore")
        self.val_df.drop(columns=[c for c in EXCLUDED_COLS if c in self.val_df.columns],
                         inplace=True, errors="ignore")

        train_pos = pd.get_dummies(self.train_df["team_position"], prefix="pos")
        val_pos = pd.get_dummies(self.val_df["team_position"], prefix="pos")
        val_pos = val_pos.reindex(columns=train_pos.columns, fill_value=0)

        self.train_df = pd.concat(
            [self.train_df.drop(columns=["team_position"]), train_pos], axis=1
        )
        self.val_df = pd.concat(
            [self.val_df.drop(columns=["team_position"]), val_pos], axis=1
        )

        y_train = self.train_df["win"].astype(float).values
        y_val = self.val_df["win"].astype(float).values
        X_train = self.train_df.drop(columns=["win"])
        X_val = self.val_df.drop(columns=["win"])

        self.mean = X_train.mean()
        self.std = X_train.std().replace(0, 1)

        X_train_norm = (X_train - self.mean) / self.std
        X_val_norm = (X_val - self.mean) / self.std

        self.X_train = torch.tensor(X_train_norm.values, dtype=torch.float32)
        self.y_train = torch.tensor(y_train, dtype=torch.float32)
        self.X_val = torch.tensor(X_val_norm.values, dtype=torch.float32)
        self.y_val = torch.tensor(y_val, dtype=torch.float32)

    def setup(self, stage=None):
        self.train_dataset = TensorDataset(self.X_train, self.y_train)
        self.val_dataset = TensorDataset(self.X_val, self.y_val)

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=4
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_dataset, batch_size=self.batch_size, shuffle=False, num_workers=4
        )

class EvaluateMLP(pl.LightningModule):
    def __init__(self, input_dim: int, lr: float = 1e-3):
        super().__init__()
        self.save_hyperparameters()

        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

        self.loss_fn = nn.BCEWithLogitsLoss()
        self.train_acc = torchmetrics.ClassificationTaskWrapper(
            torchmetrics.BinaryAccuracy()
        )
        self.val_acc = torchmetrics.ClassificationTaskWrapper(
            torchmetrics.BinaryAccuracy()
        )

    def forward(self, x):
        return self.net(x)

    def _step(self, batch, stage: str):
        x, y = batch
        logits = self(x).view(-1)
        loss = self.loss_fn(logits, y)
        preds = torch.sigmoid(logits)
        acc_metric = self.train_acc if stage == "train" else self.val_acc
        acc_metric.update(preds, y.long())
        self.log(f"{stage}_loss", loss, prog_bar=True, on_epoch=True, on_step=False)
        return loss

    def training_step(self, batch, batch_idx):
        return self._step(batch, "train")

    def on_train_epoch_end(self):
        self.log("train_acc", self.train_acc.compute(), prog_bar=True)
        self.train_acc.reset()

    def validation_step(self, batch, batch_idx):
        self._step(batch, "val")

    def on_validation_epoch_end(self):
        self.log("val_acc", self.val_acc.compute(), prog_bar=True)
        self.val_acc.reset()

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_url", required=True, help="SQLAlchemy 접속 문자열")
    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--mlruns", default="./mlruns", help="MLflow tracking URI")
    args = parser.parse_args()


    train_sql = """
        23년 시즌 2부터 24년 시즌 4
    """
    val_sql = """
        25년 시즌 1
    """

    dm = LoLPlayerDataModule(
        db_url=args.db_url,
        train_query=train_sql,
        val_query=val_sql,
        batch_size=args.batch_size,
    )
    dm.prepare_data()
    dm.setup()

    model = PlayerSkillMLP(input_dim=dm.X_train.shape[1], lr=args.lr)

    mlf_logger = MLFlowLogger(
        experiment_name="LoLMatchmaking",
        tracking_uri=f"file:{args.mlruns}",
    )

    trainer = pl.Trainer(
        max_epochs=args.epochs,
        logger=mlf_logger,
        log_every_n_steps=50,
        accelerator="auto",
    )
    trainer.fit(model, datamodule=dm)


if __name__ == "__main__":
    main()

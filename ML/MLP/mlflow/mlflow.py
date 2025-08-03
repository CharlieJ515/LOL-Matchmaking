import os, json, mlflow, torch, matplotlib.pyplot as plt, seaborn as sns
from datetime import datetime
from sklearn.metrics import confusion_matrix, classification_report
from torchinfo import summary
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

def log_metrics_dict(metrics: dict, step: int):
    for name, value in metrics.items():
        mlflow.log_metric(name, float(value), step=step)

def log_artifacts_list(files: list[tuple[str, str]]):
    for path, fname in files:
        mlflow.log_artifact(fname, artifact_path=path)

def plot_and_log(x, y, title, filename, y_label="Value", x_label="Epoch"):
    plt.figure(figsize=(4, 3))
    plt.plot(x, y)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    mlflow.log_artifact(filename, artifact_path="plots")

class MyModel(nn.Module):
    def __init__(self, embedding_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embedding_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    def forward(self, x):
        return self.net(x).squeeze(1)

def train_one_epoch(model, loader, optim):
    model.train()
    loss_fn = nn.BCEWithLogitsLoss()
    total_loss = 0
    for x, y in loader:
        optim.zero_grad()
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        optim.step()
        total_loss += loss.item() * x.size(0)
    return total_loss / len(loader.dataset)

def validate(model, loader):
    model.eval()
    loss_fn = nn.BCEWithLogitsLoss()
    total_loss, correct = 0, 0
    with torch.no_grad():
        for x, y in loader:
            logits = model(x)
            loss = loss_fn(logits, y)
            preds = torch.sigmoid(logits) > 0.5
            correct += (preds.float() == y).sum().item()
            total_loss += loss.item() * x.size(0)
    return total_loss / len(loader.dataset), correct / len(loader.dataset)

def get_all_preds(model, loader):
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for x, y in loader:
            logits = model(x)
            preds = (torch.sigmoid(logits) > 0.5).float()
            y_true.extend(y.tolist())
            y_pred.extend(preds.tolist())
    return y_true, y_pred

EXPERIMENT = "LoLMatchmaking"
PARAMS = dict(
    batch_size     = 256,
    learning_rate  = 1e-3,
    embedding_dim  = 32,
    optimizer      = "Adam",
    epochs         = 5
)

num_samples = 2000
X = torch.randn(num_samples, PARAMS["embedding_dim"])
y = torch.randint(0, 2, (num_samples,)).float()
train_ds = TensorDataset(X[:1600], y[:1600])
val_ds   = TensorDataset(X[1600:1800], y[1600:1800])
test_ds  = TensorDataset(X[1800:], y[1800:])
loader_train = DataLoader(train_ds, batch_size=PARAMS["batch_size"], shuffle=True)
loader_val   = DataLoader(val_ds, batch_size=PARAMS["batch_size"])
loader_test  = DataLoader(test_ds, batch_size=PARAMS["batch_size"])

mlflow.set_experiment(EXPERIMENT)
with mlflow.start_run(run_name=f"run_{datetime.now():%Y%m%d_%H%M%S}"):

    mlflow.log_params(PARAMS)

    model = MyModel(embedding_dim=PARAMS["embedding_dim"])
    model_summary = summary(model, input_size=(1, PARAMS["embedding_dim"]))
    with open("model_summary.txt", "w") as f:
        f.write(str(model_summary))
    mlflow.log_artifact("model_summary.txt", artifact_path="model_info")

    optimizer  = torch.optim.Adam(model.parameters(), lr=PARAMS["learning_rate"])
    scheduler  = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=PARAMS["epochs"]
    )

    train_losses, val_losses, val_accs, lrs = [], [], [], []

    for epoch in range(PARAMS["epochs"]):
        train_loss = train_one_epoch(model, loader_train, optimizer)
        val_loss,  val_acc = validate(model, loader_val)
        scheduler.step()
        lr_now = scheduler.get_last_lr()[0]

        log_metrics_dict(
            {"train_loss": train_loss, "val_loss": val_loss,
             "val_acc": val_acc, "lr": lr_now},
            step=epoch
        )

        train_losses.append(train_loss)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        lrs.append(lr_now)

    y_true, y_pred = get_all_preds(model, loader_test)

    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(4,4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.title("Confusion Matrix")
    plt.xlabel("Pred")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png")
    plt.close()

    class_report = classification_report(y_true, y_pred, output_dict=True)
    with open("per_class_metrics.json", "w") as f:
        json.dump(class_report, f, indent=2)

    plot_and_log(range(PARAMS["epochs"]), train_losses, "Train Loss",
                 "loss_train.png", y_label="Loss")
    plot_and_log(range(PARAMS["epochs"]), val_losses,   "Val Loss",
                 "loss_val.png",   y_label="Loss")
    plot_and_log(range(PARAMS["epochs"]), val_accs,     "Val Accuracy",
                 "val_acc.png",    y_label="Accuracy")
    plot_and_log(range(PARAMS["epochs"]), lrs,          "LR Schedule",
                 "lr_curve.png",   y_label="LR")

    torch.save(model.state_dict(), "model_best.pt")

    ARTIFACTS = [
        ("plots", "confusion_matrix.png"),
        ("plots", "loss_train.png"),
        ("plots", "loss_val.png"),
        ("plots", "val_acc.png"),
        ("plots", "lr_curve.png"),
        ("models", "model_best.pt"),
    ]
    log_artifacts_list(ARTIFACTS)

import os, json, mlflow, torch, matplotlib.pyplot as plt, seaborn as sns
from datetime import datetime
from sklearn.metrics import confusion_matrix, classification_report
from torchinfo import summary

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

EXPERIMENT = "LoLMatchmaking"
PARAMS = dict(
    batch_size =
    learning_rate =
    embedding_dim =
    optimizer =
    epochs =
)

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

"""
MineGuard AI - Model Evaluation & Cross-Validation Engine (Phase C5)
Computes rigorous classification metrics (Precision, Recall, F1, ROC-AUC),
generates base64 visualization plots, and executes k-fold cross validation.
"""

import io
import base64
from typing import Dict, Any, List, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve
)
from sklearn.model_selection import cross_val_score


class ModelEvaluator:
    """
    Independent model evaluation suite producing benchmark metrics and charts.
    """

    def evaluate_model(self, model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Calculates complete evaluation metrics suite on test set."""
        y_pred = model.predict(X_test)
        
        has_proba = hasattr(model, "predict_proba")
        if has_proba and len(np.unique(y_test)) > 1:
            y_proba = model.predict_proba(X_test)[:, 1]
        else:
            y_proba = y_pred.astype(float)

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

        try:
            auc = float(roc_auc_score(y_test, y_proba)) if len(np.unique(y_test)) > 1 else 1.0
        except Exception:
            auc = 1.0

        cm = confusion_matrix(y_test, y_pred).tolist()
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        return {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": auc,
            "confusion_matrix": cm,
            "classification_report": report
        }

    def plot_confusion_matrix(self, cm: List[List[int]]) -> str:
        """Renders confusion matrix heatmap and returns base64-encoded PNG."""
        fig, ax = plt.subplots(figsize=(4, 3.5))
        matrix = np.array(cm)
        cax = ax.matshow(matrix, cmap="Blues", alpha=0.8)

        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(x=j, y=i, s=str(matrix[i, j]), va="center", ha="center", fontsize=12, fontweight="bold")

        fig.colorbar(cax)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Safe/Low", "Critical/High"])
        ax.set_yticklabels(["Safe/Low", "Critical/High"])
        ax.set_xlabel("Predicted Label", fontweight="bold")
        ax.set_ylabel("True Label", fontweight="bold")
        ax.set_title("Confusion Matrix", pad=15, fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    def plot_roc_curve(self, y_test: np.ndarray, y_proba: np.ndarray) -> str:
        """Renders ROC curve and returns base64-encoded PNG."""
        fig, ax = plt.subplots(figsize=(4.5, 3.5))
        if len(np.unique(y_test)) > 1:
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            auc_val = roc_auc_score(y_test, y_proba)
            ax.plot(fpr, tpr, color="#3b82f6", lw=2, label=f"ROC (AUC = {auc_val:.2f})")
        else:
            ax.plot([0, 1], [1, 1], color="#3b82f6", lw=2, label="ROC (Perfect)")

        ax.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel("False Positive Rate", fontweight="bold")
        ax.set_ylabel("True Positive Rate", fontweight="bold")
        ax.set_title("Receiver Operating Characteristic", fontweight="bold")
        ax.legend(loc="lower right")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    def compare_models(self, models_dict: Dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> List[Dict[str, Any]]:
        """Evaluates and compares multiple models on the exact same test dataset."""
        results = []
        for name, model in models_dict.items():
            metrics = self.evaluate_model(model, X_test, y_test)
            metrics["model_name"] = name
            results.append(metrics)
        return results

    def cross_validate(self, model: Any, X: np.ndarray, y: np.ndarray, cv: int = 5) -> Dict[str, Any]:
        """Performs stratified k-fold cross validation."""
        n_samples = len(X)
        if n_samples < cv * 2:
            cv = max(2, n_samples // 2)

        underlying = getattr(model, "model", model)
        scores = cross_val_score(underlying, X, y, cv=cv, scoring="f1_weighted")

        return {
            "cv_folds": cv,
            "scores": [float(s) for s in scores],
            "mean_f1": float(np.mean(scores)),
            "std_f1": float(np.std(scores))
        }

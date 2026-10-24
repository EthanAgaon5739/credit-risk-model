
"""
model_training.py
 
Trains and compares two models on the loan default problem:
  1. Logistic Regression - simple, interpretable baseline
  2. Random Forest       - captures non-linear patterns and interactions
 
Evaluation focuses on ROC-AUC, precision and recall (not just accuracy) because
only a small share of loans default.
 
Outputs (saved to the outputs/ folder):
  model_results.csv, threshold_analysis.csv,
  roc_curves.png, confusion_matrices.png, feature_importance.png
"""
 
import os
import numpy as np
import pandas as pd
import matplotlib
 
matplotlib.use("Agg")  # save charts to files instead of opening windows
import matplotlib.pyplot as plt
 
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
    roc_curve,
)
 
from feature_engineering import build_model_data
 
OUTPUT_DIR = "outputs"
RANDOM_STATE = 42
 
 
# ─────────────────────────────────────────────
#  MODELS
# ─────────────────────────────────────────────
 
def get_models() -> dict:
    """Both models use class weights so the rare 'default' class isn't ignored."""
    return {
        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_leaf=50,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }
 
 
# ─────────────────────────────────────────────
#  EVALUATION
# ─────────────────────────────────────────────
 
def evaluate(name, model, X_test, y_test, threshold=0.5) -> dict:
    """Score a fitted model on the held-out test set."""
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= threshold).astype(int)
 
    return {
        "model": name,
        "accuracy": accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds, zero_division=0),
        "recall": recall_score(y_test, preds),
        "f1": f1_score(y_test, preds),
        "roc_auc": roc_auc_score(y_test, proba),
        "pr_auc": average_precision_score(y_test, proba),
        "_proba": proba,
        "_preds": preds,
    }
 
 
def threshold_analysis(y_test, proba) -> pd.DataFrame:
    """Show how precision/recall trade off as the decision threshold moves."""
    rows = []
    for t in [0.3, 0.4, 0.5, 0.6, 0.7]:
        preds = (proba >= t).astype(int)
        rows.append({
            "threshold": t,
            "precision": precision_score(y_test, preds, zero_division=0),
            "recall": recall_score(y_test, preds),
            "pct_of_loans_flagged": preds.mean() * 100,
        })
    return pd.DataFrame(rows)
 
 
# ─────────────────────────────────────────────
#  CHARTS
# ─────────────────────────────────────────────
 
def plot_roc_curves(results, y_test):
    plt.figure(figsize=(7, 6))
    for r in results:
        fpr, tpr, _ = roc_curve(y_test, r["_proba"])
        plt.plot(fpr, tpr, linewidth=2, label=f"{r['model']} (AUC = {r['roc_auc']:.3f})")
    plt.plot([0, 1], [0, 1], "k--", label="Random guessing")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate (Recall)")
    plt.title("ROC Curves: Loan Default Prediction")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/roc_curves.png", dpi=150)
    plt.close()
 
 
def plot_confusion_matrices(results, y_test):
    fig, axes = plt.subplots(1, len(results), figsize=(6 * len(results), 5))
    for ax, r in zip(np.atleast_1d(axes), results):
        cm = confusion_matrix(y_test, r["_preds"])
        ConfusionMatrixDisplay(cm, display_labels=["Repaid", "Default"]).plot(
            ax=ax, cmap="Blues", colorbar=False, values_format=","
        )
        ax.set_title(r["model"])
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/confusion_matrices.png", dpi=150)
    plt.close()
 
 
def plot_feature_importance(fitted_models, feature_names):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
 
    # Random Forest: built-in importance
    rf = fitted_models["Random Forest"]
    rf_imp = pd.Series(rf.feature_importances_, index=feature_names).nlargest(12)
    rf_imp.sort_values().plot(kind="barh", ax=axes[0], color="#2E86AB")
    axes[0].set_title("Random Forest: Top 12 Feature Importances")
    axes[0].set_xlabel("Importance")
 
    # Logistic Regression: standardized coefficients (sign shows direction of risk)
    lr = fitted_models["Logistic Regression"].named_steps["logisticregression"]
    coefs = pd.Series(lr.coef_[0], index=feature_names)
    top = coefs.reindex(coefs.abs().nlargest(12).index).sort_values()
    colors = ["#C0392B" if v > 0 else "#27AE60" for v in top]
    top.plot(kind="barh", ax=axes[1], color=colors)
    axes[1].set_title("Logistic Regression: Top 12 Coefficients\n(red = raises default risk, green = lowers it)")
    axes[1].set_xlabel("Standardized coefficient")
 
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/feature_importance.png", dpi=150)
    plt.close()
 
 
# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
 
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
 
    print("Building features...")
    X, y = build_model_data()
    print(f"  {X.shape[0]:,} loans, {X.shape[1]} features, default rate {y.mean() * 100:.2f}%")
 
    # Stratified split keeps the same default rate in train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
 
    baseline_acc = 1 - y_test.mean()
    print(f"\nBaseline: predicting 'no default' for everyone gives {baseline_acc * 100:.1f}% accuracy")
    print("(so accuracy alone is not a useful measure here)\n")
 
    models = get_models()
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
 
    results, fitted = [], {}
    for name, model in models.items():
        print(f"Training {name}...")
 
        # Cross-validation on the training set shows how stable the model is
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
        print(f"  3-fold CV ROC-AUC: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
 
        model.fit(X_train, y_train)
        fitted[name] = model
 
        res = evaluate(name, model, X_test, y_test)
        res["cv_roc_auc_mean"] = cv_scores.mean()
        res["cv_roc_auc_std"] = cv_scores.std()
        results.append(res)
 
    # ── Results table ──
    table = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in results])
    table = table.set_index("model").round(4)
    table.to_csv(f"{OUTPUT_DIR}/model_results.csv")
 
    print("\n" + "=" * 70)
    print("  TEST SET RESULTS (threshold = 0.5)")
    print("=" * 70)
    print(table.T.to_string())
 
    best = max(results, key=lambda r: r["roc_auc"])
    print(f"\nBest model by ROC-AUC: {best['model']} ({best['roc_auc']:.4f})")
 
    # ── Threshold trade-off for the best model ──
    thresholds = threshold_analysis(y_test, best["_proba"]).round(4)
    thresholds.to_csv(f"{OUTPUT_DIR}/threshold_analysis.csv", index=False)
    print(f"\nThreshold trade-offs for {best['model']}:")
    print(thresholds.to_string(index=False))
 
    # ── Charts ──
    plot_roc_curves(results, y_test)
    plot_confusion_matrices(results, y_test)
    plot_feature_importance(fitted, X.columns)
    print(f"\nSaved charts and tables to the '{OUTPUT_DIR}/' folder.")
 
 
if __name__ == "__main__":
    main()
 
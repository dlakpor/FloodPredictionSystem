# train_models.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, StackingRegressor, StackingClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, roc_auc_score, accuracy_score
import xgboost as xgb
import joblib
import os

def train():
    # Use absolute paths relative to this script
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    IN = os.path.join(BASE_DIR, "data", "features_for_ml.csv")
    MODEL_DIR = os.path.join(BASE_DIR, "models")
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading features...")
    if not os.path.exists(IN):
        print(f"ERROR: {IN} not found.")
        return

    df = pd.read_csv(IN, parse_dates=["date"])

    # Remove invalid rows
    df = df.dropna(subset=["next_tp", "flood_label"])

    # Features
    feature_cols = [c for c in df.columns if c.startswith("tp_lag") or 
                    c in ["tp_3d_sum","tp_7d_sum","t2m_7d_mean"]]

    # Validate feature columns exist
    for f in feature_cols:
        if f not in df.columns:
            raise ValueError(f"ERROR: Missing feature column: {f}")

    X = df[feature_cols]
    y_reg = df["next_tp"]
    y_clf = df["flood_label"]

    # Time-aware split
    dates = sorted(df["date"].unique())
    split_idx = int(len(dates) * 0.8)

    train_dates = set(dates[:split_idx])
    train_mask = df["date"].isin(train_dates)

    X_train, X_test = X[train_mask], X[~train_mask]
    y_reg_train, y_reg_test = y_reg[train_mask], y_reg[~train_mask]
    y_clf_train, y_clf_test = y_clf[train_mask], y_clf[~train_mask]

    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ----------------------------
    # 1. Baseline: Random Forest
    # ----------------------------
    print("\n--- Training Model 1: Random Forest (Baseline) ---")
    rf_reg = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    rf_reg.fit(X_train_scaled, y_reg_train)
    
    rf_clf = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight="balanced", random_state=42)
    rf_clf.fit(X_train_scaled, y_clf_train)

    # ----------------------------
    # 2. Standalone: XGBoost
    # ----------------------------
    print("\n--- Training Model 2: XGBoost (Modern Standalone) ---")
    xgb_reg = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
    xgb_reg.fit(X_train_scaled, y_reg_train)
    
    xgb_clf = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, scale_pos_weight=5, random_state=42)
    xgb_clf.fit(X_train_scaled, y_clf_train)

    # ----------------------------
    # 3. Hybrid: Hybrid Stacking (XGBoost + Neural Network)
    # ----------------------------
    print("\n--- Training Model 3: Hybrid (XGBoost + MLP Stacking) ---")
    
    # Hybrid Regressor
    reg_estimators = [
        ('xgb', xgb.XGBRegressor(n_estimators=50, max_depth=5, random_state=42)),
        ('mlp', MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42))
    ]
    hybrid_reg = StackingRegressor(estimators=reg_estimators, final_estimator=Ridge())
    hybrid_reg.fit(X_train_scaled, y_reg_train)

    # Hybrid Classifier
    clf_estimators = [
        ('xgb', xgb.XGBClassifier(n_estimators=50, max_depth=5, random_state=42)),
        ('mlp', MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42))
    ]
    hybrid_clf = StackingClassifier(estimators=clf_estimators, final_estimator=LogisticRegression())
    hybrid_clf.fit(X_train_scaled, y_clf_train)

    # Evaluate and Save
    models = {
        "rf": (rf_reg, rf_clf),
        "xgb": (xgb_reg, xgb_clf),
        "hybrid": (hybrid_reg, hybrid_clf)
    }

    for name, (reg, clf) in models.items():
        print(f"\nEvaluating {name.upper()}...")
        p_reg = reg.predict(X_test_scaled)
        p_proba = clf.predict_proba(X_test_scaled)[:, 1]
        
        rmse = mean_squared_error(y_reg_test, p_reg) ** 0.5
        auc = roc_auc_score(y_clf_test, p_proba)
        acc = accuracy_score(y_clf_test, (p_proba >= 0.5).astype(int))
        
        print(f"[{name}] RMSE: {rmse:.4f}, AUC: {auc:.4f}, Accuracy: {acc:.4f}")

        # Metadata
        metadata = {
            "name": f"{name.upper()} Model",
            "type": "Ensemble" if name == "hybrid" else "Standalone",
            "version": "1.0",
            "features": feature_cols,
            "scaler": scaler,
            "model": reg if "regressor" in name else None # Placeholder, we save actual below
        }

        joblib.dump({"model": reg, "scaler": scaler, "features": feature_cols, "metadata": {**metadata, "task": "regression"}}, 
                    os.path.join(MODEL_DIR, f"{name}_regressor.joblib"))
        joblib.dump({"model": clf, "scaler": scaler, "features": feature_cols, "metadata": {**metadata, "task": "classification"}}, 
                    os.path.join(MODEL_DIR, f"{name}_classifier.joblib"))

    print("\n✅ All models trained and saved to", MODEL_DIR)

if __name__ == "__main__":
    train()

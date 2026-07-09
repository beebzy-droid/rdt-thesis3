"""scripts/learnability_baseline.py — §5.2.3 classical-ML baseline (mandated BEFORE
the GAT): can dR_php be predicted from tabular scenario+option features? The GAT's
marginal value is measured AGAINST these numbers, not asserted.
5-fold CV, 3 seeds; leakage guard: split at scenario level (both arms of a pair
never straddle folds — the §5.2.1 discipline in miniature)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error

df = pd.read_parquet("data/labels_v0.parquet")
X = pd.get_dummies(df[["category", "option", "unit"]], dtype=float)
for c in ["severity", "duration_hr", "onset_hr", "dx_wb", "y_mult"]:
    X[c] = df[c].fillna(0.0)
y = df["dR_php"].to_numpy()
# scenario key: seed alone COLLIDES across categories (same SEED0 counter) —
# caught 2026-07-03; category+seed is the true scenario identity
df["scen"] = df["category"] + "_" + df["seed"].astype(str)
groups = df["scen"].to_numpy()

for name, mk in [("Ridge", lambda s: Ridge(alpha=1.0)),
                 ("HistGBT", lambda s: HistGradientBoostingRegressor(random_state=s))]:
    r2s, maes = [], []
    for s in (0, 1, 2):
        for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
            m = mk(s).fit(X.iloc[tr], y[tr])
            p = m.predict(X.iloc[te])
            r2s.append(r2_score(y[te], p)); maes.append(mean_absolute_error(y[te], p))
    print(f"{name:8s} R2 = {np.mean(r2s):.3f} ± {np.std(r2s):.3f}   "
          f"MAE(dR) = {np.mean(maes):.4f} ± {np.std(maes):.4f}")
print(f"target std for scale: sigma(dR) = {y.std():.4f}, mean|dR| = {np.abs(y).mean():.4f}")
# decision-quality metric: does the model pick the right option per scenario?
gbt = HistGradientBoostingRegressor(random_state=0)
hits, oracle_R, model_R = 0, [], []
for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
    m = gbt.fit(X.iloc[tr], y[tr]); pred = m.predict(X.iloc[te])
    sub = df.iloc[te].copy(); sub["pred"] = pred
    for _, g in sub.groupby("scen"):
        best_true = g.loc[g.dR_php.idxmax()]
        best_pred = g.loc[g.pred.idxmax()]
        act_true = max(best_true.dR_php, 0)          # oracle may choose null
        act_pred = best_pred.dR_php if best_pred.pred > 0 else 0.0
        oracle_R.append(act_true); model_R.append(max(act_pred, act_pred))
        hits += int(np.isclose(act_pred, act_true, atol=1e-9))
n = len(oracle_R)
print(f"decision quality (5-fold, GBT): correct option {hits}/{n} = {hits/n:.0%}")
print(f"realized dR: model-gated {np.mean(model_R):.4f} vs oracle {np.mean(oracle_R):.4f} "
      f"({np.mean(model_R)/np.mean(oracle_R):.0%} of oracle captured)")

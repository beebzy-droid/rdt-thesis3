"""scripts/loto.py — Leave-One-Option-Out generalization (the N2-decisive test).
Train on 3 options, predict the held-out option's dR. Models:
  flat-GBT      : flattened X_V+X_E+dG (Finding-#13 deployable baseline)
  blind-GBT     : same minus dG (option-identity-blind state prior = transfer floor)
  GAT           : rdt_core.gat_jax (unseen edge seen via graph position/features)
Metrics: R2, MAE, Spearman rank corr, sign accuracy (helps: y>0.005).
Usage: python scripts/loto.py <held_out_option> [gat|gbt]"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error

d = np.load('data/gat_dataset_v1.npz', allow_pickle=True)
XV, XE, DG, y, ei = d['X_V'], d['X_E'], d['dG'], d['y'], d['edge_index']
idx = pd.read_parquet('data/gat_dataset_v1_index.parquet')
opt = sys.argv[1]; mode = sys.argv[2] if len(sys.argv) > 2 else "gbt"
tr = np.where(idx.option != opt)[0]; te = np.where(idx.option == opt)[0]

def report(tag, pred):
    sa = np.mean((pred > 0.005) == (y[te] > 0.005))
    rho = spearmanr(pred, y[te]).statistic if np.std(pred) > 1e-12 else 0.0
    row = dict(held_out=opt, model=tag, r2=r2_score(y[te], pred),
               mae=mean_absolute_error(y[te], pred), spearman=rho, sign_acc=sa,
               n_te=len(te))
    print(f"{opt:12s} {tag:9s} R2={row['r2']:7.3f} MAE={row['mae']:.4f} "
          f"rho={rho:6.3f} sign={sa:.2f}")
    out = pathlib.Path('data/loto_results.csv')
    pd.DataFrame([row]).to_csv(out, mode='a', header=not out.exists(), index=False)

if mode == "gbt":
    Xf = np.concatenate([XV.reshape(len(y), -1), XE.reshape(len(y), -1), DG], 1)
    Xb = np.concatenate([XV.reshape(len(y), -1), XE.reshape(len(y), -1)], 1)
    report("flat-GBT", HistGradientBoostingRegressor(random_state=0)
           .fit(Xf[tr], y[tr]).predict(Xf[te]))
    report("blind-GBT", HistGradientBoostingRegressor(random_state=0)
           .fit(Xb[tr], y[tr]).predict(Xb[te]))
else:
    from rdt_core import gat_jax as gj
    report("GAT", gj.train(XV, XE, DG, y, ei, tr, te, seed=0, epochs=400, lr=3e-3))

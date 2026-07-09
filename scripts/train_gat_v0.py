"""scripts/train_gat_v0.py — GAT prototype evaluation, §5.2 protocol miniature.
Same GroupKFold scenario-disjoint splits and records as the Finding-#13 baselines.
Bars: state-only flat GBT R2=0.623 (deployable info set); oracle-tabular 0.868
(reference only — contaminated with future information).
Usage: python scripts/train_gat_v0.py <seed>   (results appended to CSV)"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error
from rdt_core import gat_jax as gj

seed = int(sys.argv[1])
d = np.load('data/gat_dataset_v0.npz', allow_pickle=True)
XV, XE, DG, y, ei = d['X_V'], d['X_E'], d['dG'], d['y'], d['edge_index']
groups = pd.read_parquet('data/gat_dataset_v0_index.parquet').scen.to_numpy()

rows, t0 = [], time.perf_counter()
for k, (tr, te) in enumerate(GroupKFold(5).split(XV, y, groups)):
    pred = gj.train(XV, XE, DG, y, ei, tr, te, seed=seed, epochs=400, lr=3e-3)
    rows.append(dict(seed=seed, fold=k, r2=r2_score(y[te], pred),
                     mae=mean_absolute_error(y[te], pred)))
    print(f"seed {seed} fold {k}: R2={rows[-1]['r2']:.3f} MAE={rows[-1]['mae']:.4f} "
          f"({time.perf_counter()-t0:.0f}s)")
df = pd.DataFrame(rows)
out = pathlib.Path('data/gat_v0_cv.csv')
df.to_csv(out, mode='a', header=not out.exists(), index=False)

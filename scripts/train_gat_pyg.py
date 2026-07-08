"""scripts/train_gat_pyg.py — Production GAT (PyTorch Geometric) + N2 onset harness.

Mirrors the audited JAX prototype (rdt_core/gat_jax.py) exactly: GATv2 with edge
features (ΔG appended as edge channel), residual message passing, readout =
[global mean ‖ ΔG-endpoint pool] → MLP → standardized-target Huber regression.
Runs on the reference GPU; deliberately torch_scatter-free (PyG ≥ 2.5 native ops).

MODES
  --mode smoke              20-record overfit gate (run FIRST; asserts R² > 0.8)
  --mode cv                 5-fold scenario-disjoint CV, --seeds S
  --mode loto --held X      leave-one-option-out (F#15/#18 protocol)
  --mode onset              N2 curve: k ∈ {3,4,5,6} option-subset training,
                            transfer to held-out options, GAT vs flat GBT paired
                            on identical splits → data/n2_onset.csv

INSTALL (reference machine):   pip install -r requirements-gpu.txt
"""
import argparse, itertools, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GATv2Conv, global_mean_pool

DEV = "cuda" if torch.cuda.is_available() else "cpu"


# ---------------------------------------------------------------- data
def load_dataset():
    d = np.load("data/gat_dataset_v1.npz", allow_pickle=True)
    idx = pd.read_parquet("data/gat_dataset_v1_index.parquet")
    ei = torch.tensor(d["edge_index"], dtype=torch.long)
    data = []
    for i in range(len(d["y"])):
        data.append(Data(
            x=torch.tensor(d["X_V"][i], dtype=torch.float),
            edge_index=ei,
            edge_attr=torch.tensor(
                np.concatenate([d["X_E"][i], d["dG"][i][:, None]], 1),
                dtype=torch.float),
            dg=torch.tensor(d["dG"][i], dtype=torch.float),
            y=torch.tensor([d["y"][i]], dtype=torch.float)))
    return data, idx, d


class RdtGAT(nn.Module):
    def __init__(self, d_v=12, d_e=9, dim=64, heads=4, layers=2):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(d_v, dim), nn.ELU())
        self.convs = nn.ModuleList([
            GATv2Conv(dim, dim // heads, heads=heads, edge_dim=d_e)
            for _ in range(layers)])
        self.head = nn.Sequential(nn.Linear(2 * dim, 64), nn.ELU(),
                                  nn.Dropout(0.1), nn.Linear(64, 1))

    def forward(self, b):
        h = self.enc(b.x)
        for conv in self.convs:
            h = torch.nn.functional.elu(conv(h, b.edge_index, b.edge_attr)) + h
        g_mean = global_mean_pool(h, b.batch)                       # [B, dim]
        # ΔG-endpoint pool (torch_scatter-free): edge -> graph id via src node
        src, dst = b.edge_index
        eg = b.batch[src]                                           # [E_tot]
        wsum = torch.zeros(g_mean.size(0), device=h.device).index_add_(
            0, eg, b.dg) + 1e-9
        w = (b.dg / wsum[eg]).unsqueeze(1)
        g_delta = torch.zeros_like(g_mean).index_add_(0, eg, w * (h[src] + h[dst]))
        return self.head(torch.cat([g_mean, g_delta], 1)).squeeze(1)


def fit_eval(data, tr, te, seed=0, epochs=300, lr=3e-3, dim=64, heads=4, layers=2):
    torch.manual_seed(seed)
    y_all = np.array([float(d.y) for d in data])
    mu, sd = y_all[tr].mean(), y_all[tr].std() + 1e-9
    model = RdtGAT(dim=dim, heads=heads, layers=layers).to(DEV)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
    tr_loader = DataLoader([data[i] for i in tr], batch_size=256, shuffle=True)
    te_loader = DataLoader([data[i] for i in te], batch_size=512)
    huber = nn.HuberLoss(delta=1.0)
    model.train()
    for _ in range(epochs):
        for b in tr_loader:
            b = b.to(DEV)
            opt.zero_grad()
            loss = huber(model(b), (b.y.squeeze(1) - mu) / sd)
            loss.backward(); opt.step()
    model.eval()
    preds = []
    with torch.no_grad():
        for b in te_loader:
            preds.append(model(b.to(DEV)).cpu().numpy() * sd + mu)
    return np.concatenate(preds)


def metrics(y, p):
    from sklearn.metrics import r2_score, mean_absolute_error
    from scipy.stats import spearmanr
    rho = spearmanr(p, y).statistic if np.std(p) > 1e-12 else 0.0
    return dict(r2=r2_score(y, p), mae=mean_absolute_error(y, p), rho=rho)


def flat_gbt(d, tr, te):
    from sklearn.ensemble import HistGradientBoostingRegressor
    X = np.concatenate([d["X_V"].reshape(len(d["y"]), -1),
                        d["X_E"].reshape(len(d["y"]), -1), d["dG"]], 1)
    return HistGradientBoostingRegressor(random_state=0).fit(
        X[tr], d["y"][tr]).predict(X[te])


# ---------------------------------------------------------------- modes
def mode_smoke(data, idx, d):
    rng = np.random.default_rng(1)
    sub = rng.choice(len(data), 20, replace=False)
    p = fit_eval(data, sub, sub, epochs=500)
    m = metrics(np.array([float(data[i].y) for i in sub]), p)
    print(f"smoke overfit: R2={m['r2']:.3f} (gate > 0.8) on {DEV}")
    assert m["r2"] > 0.8, "SMOKE FAIL — do not proceed to sweeps"
    print("SMOKE PASS")


def mode_cv(data, idx, d, seeds):
    from sklearn.model_selection import GroupKFold
    y = d["y"]; groups = idx.scen.to_numpy()
    rows = []
    for s in range(seeds):
        for k, (tr, te) in enumerate(GroupKFold(5).split(y, y, groups)):
            m = metrics(y[te], fit_eval(data, tr, te, seed=s))
            rows.append(dict(seed=s, fold=k, **m))
            print(f"seed {s} fold {k}: R2={m['r2']:.3f}")
    df = pd.DataFrame(rows)
    df.to_csv("data/gat_pyg_cv.csv", index=False)
    print(f"\nCV: R2 = {df.r2.mean():.3f} ± {df.r2.std():.3f} "
          f"(bars: flat 0.623, jax-GAT 0.644)")


def mode_loto(data, idx, d, held):
    tr = np.where(idx.option != held)[0]
    te = np.where(idx.option == held)[0]
    m = metrics(d["y"][te], fit_eval(data, tr, te))
    mg = metrics(d["y"][te], flat_gbt(d, tr, te))
    print(f"LOTO {held}: GAT R2={m['r2']:.3f} rho={m['rho']:.3f} | "
          f"flat R2={mg['r2']:.3f} rho={mg['rho']:.3f}")


def mode_onset(data, idx, d, seeds, subsets_per_k=8):
    """N2 curve: transfer quality vs training-option diversity k."""
    opts = sorted(idx.option.unique())
    y = d["y"]
    rng = np.random.default_rng(0)
    rows = []
    for k in range(3, len(opts)):
        combos = list(itertools.combinations(opts, k))
        rng.shuffle(combos)
        for ci, combo in enumerate(combos[:subsets_per_k]):
            tr = np.where(idx.option.isin(combo))[0]
            te = np.where(~idx.option.isin(combo))[0]
            for s in range(seeds):
                m = metrics(y[te], fit_eval(data, tr, te, seed=s))
                rows.append(dict(k=k, subset=ci, seed=s, model="GAT", **m))
            mg = metrics(y[te], flat_gbt(d, tr, te))
            rows.append(dict(k=k, subset=ci, seed=0, model="flat", **mg))
            print(f"k={k} subset={ci}: GAT R2={rows[-2]['r2']:.3f} "
                  f"flat R2={mg['r2']:.3f}")
    df = pd.DataFrame(rows)
    df.to_csv("data/n2_onset.csv", index=False)
    g = df.groupby(["k", "model"])[["r2", "rho"]].mean().round(3)
    print("\nN2 generalization-onset curve (transfer to held-out options):")
    print(g.to_string())
    print("\nInterpretation: onset = k where GAT transfer R2 turns positive AND "
          "exceeds flat; at k<=6 on the current library the null is expected "
          "(F#18) — the full-scale library extends this curve rightward.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="smoke",
                    choices=["smoke", "cv", "loto", "onset"])
    ap.add_argument("--held", default="solar_train")
    ap.add_argument("--seeds", type=int, default=3)
    a = ap.parse_args()
    data, idx, d = load_dataset()
    print(f"dataset: {len(data)} graphs | device: {DEV}")
    {"smoke": lambda: mode_smoke(data, idx, d),
     "cv": lambda: mode_cv(data, idx, d, a.seeds),
     "loto": lambda: mode_loto(data, idx, d, a.held),
     "onset": lambda: mode_onset(data, idx, d, a.seeds)}[a.mode]()

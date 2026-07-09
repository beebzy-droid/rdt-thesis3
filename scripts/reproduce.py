"""scripts/reproduce.py — one-command reproducibility harness (§5.6, §10.4).

Regenerates derived artifacts from committed inputs in the correct order and
verifies determinism. The GBT screen is REBUILT from its training recipe rather
than loaded from a committed pickle — a pickled model is version-fragile
(sklearn pin skew corrupts it silently); the recipe + a pinned sklearn + a fixed
seed is the reproducible artifact.

Steps (each optional via flags; default runs all that inputs allow):
  --screen    rebuild data/gbt_screen_v1.pkl from gat_dataset_v1 (seed 0),
              assert byte-identical predictions across two independent fits
  --figures   run make_figures.py (renders whatever data sources are present)
  --provenance run check_provenance.py SYNC gate
  --all       (default) all of the above

Determinism contract: two HistGBT fits with the same seed on the same data must
produce identical predictions. If they do not, the environment is not pinned
correctly and no downstream number is reproducible — this script fails loudly.
"""
import argparse, hashlib, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np


def rebuild_screen():
    from sklearn.ensemble import HistGradientBoostingRegressor
    import pickle, sklearn
    d = np.load("data/gat_dataset_v1.npz", allow_pickle=True)
    X = np.concatenate([d["X_V"].reshape(len(d["y"]), -1),
                        d["X_E"].reshape(len(d["y"]), -1), d["dG"]], 1)

    def fit_predict():
        m = HistGradientBoostingRegressor(random_state=0).fit(X, d["y"])
        return m, m.predict(X)

    m1, p1 = fit_predict()
    _, p2 = fit_predict()
    h1 = hashlib.sha256(p1.tobytes()).hexdigest()[:16]
    h2 = hashlib.sha256(p2.tobytes()).hexdigest()[:16]
    print(f"  sklearn {sklearn.__version__} | fit1 {h1} | fit2 {h2}")
    if h1 != h2:
        sys.exit("DETERMINISM FAIL — same-seed fits differ; environment not pinned")
    out = pathlib.Path("data/gbt_screen_v1.pkl")
    out.write_bytes(pickle.dumps(m1))
    print(f"  screen rebuilt deterministically -> {out} (R²_train "
          f"{m1.score(X, d['y']):.3f})")


def run(script, *args):
    r = subprocess.run([sys.executable, f"scripts/{script}", *args],
                       capture_output=True, text=True)
    print(r.stdout.rstrip())
    if r.returncode != 0:
        print(r.stderr.rstrip()); sys.exit(f"{script} failed")


def main():
    ap = argparse.ArgumentParser()
    for f in ("screen", "figures", "provenance", "all"):
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args()
    do_all = a.all or not any([a.screen, a.figures, a.provenance])
    if a.screen or do_all:
        print("[1/3] rebuilding GBT screen (deterministic)")
        rebuild_screen()
    if a.provenance or do_all:
        print("[2/3] provenance sync gate")
        run("check_provenance.py")
    if a.figures or do_all:
        print("[3/3] regenerating figures")
        run("make_figures.py")
    print("reproduce: OK")


if __name__ == "__main__":
    main()

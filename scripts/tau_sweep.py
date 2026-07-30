"""scripts/tau_sweep.py — transition time as a design axis.

The breakeven theory (thesis/theory_transition_dynamics.md, Proposition 1) states

    D*_k = tau_k + c_k / gamma_k

which makes a sharp, falsifiable prediction: the breakeven duration should move
with the transition timescale at UNIT SLOPE, dD*/dtau = 1, provided the switching
cost c_k and rescue margin gamma_k are not themselves strong functions of tau.
Any other slope means the decomposition is wrong or incomplete.

This experiment sweeps the dominant transition timescale (dryer residence,
tau_dry) across the range documented in provenance.yaml (24-36 h authoritative
envelope, extended here to 12-48 h to get leverage on the slope), regenerates
paired option-versus-null labels at each value, re-estimates D* per option, and
regresses D* on tau.

Secondary outputs, both of which matter for the regional design criterion of
Section 6 of the theory document:
  - the number of options that are CONDITIONAL (D* > 0) at each tau, which the
    theory predicts grows as tau grows
  - Pr(D > D*) under the sampled disruption distribution, which is the quantity
    the criterion turns on and which falls as tau grows

Design notes carried from earlier Windows failures: jobs are self-contained
tuples (no parent-process global mutation, which is invisible to spawned
workers), the pool is forced to spawn context, and rdt_core._console is imported
so glyph output cannot crash a cp1252 console.

Usage:
    python scripts/tau_sweep.py --taus 12,18,24,30,36,48 --cats D1,D3,D4,D8 \
        --n 40 --workers 12
    python scripts/tau_sweep.py --analyze
"""
import argparse
import glob
import importlib.util
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)

import numpy as np
import pandas as pd

# Two option families, and the distinction turned out to matter (see the
# tau-specificity finding in thesis/theory_transition_dynamics.md Section 5.1).
#
# CONTROL-INPUT options act on the reference DAE via binary control inputs. None
# of them routes material through the dryer: wet_route bypasses it (F_wet_raw =
# u_wet * (F_kernel - F_kernel_dry)), copra_buy feeds the buffer directly, and
# crude_bypass acts on tank output downstream of it. Their transition timescale
# is therefore NOT tau_dry, and sweeping tau_dry against them tests nothing.
OPTIONS_CONTROL = {"crude_bypass": dict(u_crude=1.0),
                   "wet_route":    dict(u_wet=1.0),
                   "copra_buy":    dict(u_buy=1.0)}

# TOPOLOGY options act through the graph-to-DAE compiler. solar_train activates
# five additional dryer-B compartments, so its transition IS gated by the dryer
# residence and it is the correct test of the unit-slope prediction.
OPTIONS_TOPO = {
    "solar_train": [("V02_CRACKING", "V03B_SOLAR"), ("V03B_SOLAR", "BUF_COPRA")],
    "nut_sale":    [("V01_RECEIVING", "SNK_NUT_SALE")],
}
OPTIONS = OPTIONS_CONTROL  # default path; --path topology selects the other
SEED0 = 31415
R_WIN = 72.0
OUT = pathlib.Path("data/tau_sweep")


def _load_gen_pilot():
    """gen_pilot carries run_one and the DT/DAYS constants. Loaded by path so the
    sweep does not depend on scripts/ being importable as a package."""
    here = pathlib.Path(__file__).parent
    spec = importlib.util.spec_from_file_location("gp", here / "gen_pilot.py")
    gp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gp)
    return gp


def run_cell(job):
    """One (tau, category) cell. Self-contained so it survives spawn."""
    tau, cat, n_scen, path, cold = job
    OUT.mkdir(parents=True, exist_ok=True)
    tag = ("crudecom" if path == "crude" else ("cold" if cold else "hot"))
    out = OUT / f"tau{tau:05.1f}_{cat}_{path}_{tag}.parquet"
    if out.exists():
        return f"tau={tau:5.1f} {cat} skip (exists)"

    import casadi as ca
    from rdt_core.plant_dae import PlantParams, build_plant_dae, wb2db
    from rdt_core.disruptions import sample
    gp = _load_gen_pilot()

    # tau enters ONLY through the plant parameters; everything downstream is rebuilt
    if path == "crude":
        # Sweep the SUBSTITUTIVE option's own commissioning time constant. This
        # is the tau of Proposition 1 for that option; tau_dry is not, which is
        # why the earlier sweeps could not move the breakeven.
        p = PlantParams(tau_com_crude=float(tau), cold_start=True)
    else:
        p = PlantParams(tau_dry=float(tau), cold_start=bool(cold))
    dae, out_fn = build_plant_dae(p)
    intg = ca.integrator("P", "idas", dae, 0.0, gp.DT,
                         {"abstol": 1e-8, "reltol": 1e-8})
    F0 = p.nominal_nut_feed()
    x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                         [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0],
                         [0, 0]])
    if getattr(p, "cold_start", False):
        # a_crude starts at zero: the off-take is not yet lined up
        x0 = np.concatenate([x0, [0.0]])
    z0 = np.zeros(2)

    rows, t0 = [], time.perf_counter()
    if path == "topology":
        return _run_topology_cell(tau, cat, n_scen, out, p, F0, t0, cold)
    for dp in sample(cat, n_scen, SEED0):
        _, R0, _, _, V0 = gp.run_one(dp, p, intg, out_fn, F0, x0, z0)
        opts = ({"crude_bypass": dict(u_crude=1.0)} if path == "crude"
                else OPTIONS_CONTROL)
        for name, u in opts.items():
            _, R1, _, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x0, z0, **u)
            rows.append(dict(tau_dry=float(tau), category=cat, seed=dp.seed,
                             severity=dp.severity, duration_hr=dp.duration_hr,
                             onset_hr=dp.onset_hr, option=name,
                             R_null=R0, R_opt=R1, dR=R1 - R0, V0_php_hr=V0,
                             data_class="SYNTHETIC/physics-forward-model"))
    pd.DataFrame(rows).to_parquet(out, index=False)
    return (f"tau={tau:5.1f} {cat} done {len(rows):4d} labels "
            f"{time.perf_counter()-t0:5.0f}s")


def _run_topology_cell(tau, cat, n_scen, out, p, F0, t0, cold=False):
    """Topology-path cell: options activate candidate edges through the compiler,
    so a change that adds dryer capacity has its transition gated by tau_dry.
    Reuses the switch-at-decision protocol of scripts/gen_labels_topo.py."""
    import casadi as ca
    from rdt_core.plant_dae import wb2db
    from rdt_core.disruptions import sample
    from rdt_core import icpc_graph as icpc
    from rdt_core.compiler import compile_plant, apply_change, warm_start_map
    here = pathlib.Path(__file__).parent
    spec = importlib.util.spec_from_file_location("glt", here / "gen_labels_topo.py")
    glt = importlib.util.module_from_spec(spec); spec.loader.exec_module(glt)

    G0 = glt.gmax_inactive()
    c0 = compile_plant(G0, p)
    mk = lambda c: ca.integrator("P", "idas", c.dae, 0.0, glt.DT,
                                 {"abstol": 1e-8, "reltol": 1e-8})
    i0 = mk(c0)
    x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                         [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0],
                         [0, 0]])
    arms = {}
    for name, edges in OPTIONS_TOPO.items():
        c1 = compile_plant(apply_change(glt.gmax_inactive(), edges), p)
        # Cold start relies on warm_start_map defaulting absent states to 0.0:
        # a_solar is not supplied, so the train commissions from zero availability.
        # Hot start additionally pre-fills the new compartments at inlet moisture.
        defaults = {f"x_dryB_{i}": wb2db(p.x_in_wb) for i in range(5)}
        x1 = warm_start_map(x0, c0.state_names, c1.state_names, defaults)
        arms[name] = (c1, mk(c1), x1, c1.state_names)
    arm0 = (c0, i0, x0, c0.state_names)

    rows = []
    for dp in sample(cat, n_scen, SEED0):
        R0 = glt.run(arm0, None, dp, F0)
        for name, arm1 in arms.items():
            R1 = glt.run(arm0, arm1, dp, F0)
            rows.append(dict(tau_dry=float(tau), category=cat, seed=dp.seed,
                             severity=dp.severity, duration_hr=dp.duration_hr,
                             onset_hr=dp.onset_hr, option=name,
                             R_null=R0, R_opt=R1, dR=R1 - R0, V0_php_hr=np.nan,
                             data_class="SYNTHETIC/physics-forward-model"))
    pd.DataFrame(rows).to_parquet(out, index=False)
    return (f"tau={tau:5.1f} {cat} topology done {len(rows):4d} labels "
            f"{time.perf_counter()-t0:5.0f}s")


def fit_dstar(dur, dR, T=R_WIN):
    """Breakeven from the below-horizon branch (Proposition 1)."""
    m = dur < T
    if m.sum() < 8:
        return np.nan, np.nan
    slope, icept = np.polyfit(dur[m], dR[m], 1)
    return (-icept / slope if abs(slope) > 1e-15 else np.nan), slope


def analyze(boot=4000):
    files = sorted(glob.glob(str(OUT / "*.parquet")))
    if not files:
        sys.exit("no tau_sweep shards; run without --analyze first")
    frames = []
    for f in files:
        fr = pd.read_parquet(f)
        stem = pathlib.Path(f).stem
        fr["contract"] = ("crude_com" if stem.endswith("_crudecom")
                          else ("cold" if stem.endswith("_cold") else "hot"))
        fr["path"] = "topology" if "topology" in stem else "control"
        frames.append(fr)
    d = pd.concat(frames, ignore_index=True)
    taus = np.sort(d.tau_dry.unique())
    print(f"loaded {len(d)} labels over tau in {list(taus)} h, "
          f"{d.option.nunique()} options\n")

    print("PROPOSITION 1 PREDICTION: dD*/dtau = 1 (unit slope)\n")
    rows = []
    for opt, contract in sorted(set(zip(d.option, d.contract))):
        for tau in taus:
            s = d[(d.option == opt) & (d.contract == contract) & (d.tau_dry == tau)]
            ds, sl = fit_dstar(s.duration_hr.to_numpy(), s.dR.to_numpy())
            n_cond = int(ds > 0) if np.isfinite(ds) else 0
            p_exc = float((s.duration_hr > ds).mean()) if np.isfinite(ds) else np.nan
            rows.append(dict(option=opt, contract=contract, tau=tau, D_star=ds,
                             slope=sl, conditional=n_cond, p_exceed=p_exc,
                             n=len(s)))
    tab = pd.DataFrame(rows)

    hdr = f"{'option/contract':>20} " + " ".join(f"{t:>8.0f}" for t in taus) + f" {'dD*/dtau':>10} {'95% CI':>18}"
    print(hdr); print("-" * len(hdr))
    rng = np.random.default_rng(0)
    for opt, contract in sorted(set(zip(tab.option, tab.contract))):
        s = tab[(tab.option == opt) & (tab.contract == contract)].sort_values("tau")
        cells = " ".join(f"{v:8.1f}" if np.isfinite(v) else "     n/a"
                         for v in s.D_star)
        ok = s.D_star.notna()
        if ok.sum() >= 3:
            x, y = s.tau[ok].to_numpy(), s.D_star[ok].to_numpy()
            slope = np.polyfit(x, y, 1)[0]
            bs = []
            for _ in range(boot):
                i = rng.integers(0, len(x), len(x))
                if len(np.unique(x[i])) >= 2:
                    bs.append(np.polyfit(x[i], y[i], 1)[0])
            lo, hi = (np.percentile(bs, [2.5, 97.5]) if len(bs) > 100
                      else (np.nan, np.nan))
            ci = f"[{lo:7.2f},{hi:7.2f}]"
        else:
            slope, ci = np.nan, "       n/a        "
        print(f"{opt+'/'+contract:>20} {cells} {slope:10.2f} {ci:>18}")

    tab.to_csv("data/tau_sweep_estimates.csv", index=False)

    # --- unit-slope verdict ---
    print()
    verdicts = []
    for opt, contract in sorted(set(zip(tab.option, tab.contract))):
        s = tab[(tab.option == opt) & (tab.contract == contract)].dropna(subset=["D_star"])
        if len(s) >= 3:
            sl = np.polyfit(s.tau, s.D_star, 1)[0]
            verdicts.append((f"{opt}/{contract}", sl))
    if verdicts:
        med = float(np.median([v for _, v in verdicts]))
        print(f"UNIT-SLOPE TEST: median dD*/dtau across options = {med:.2f}")
        print("  Proposition 1 predicts 1.00. Slopes near 1 confirm the tau + c/gamma")
        print("  decomposition. A slope near 0 would mean the breakeven is set by")
        print("  economics alone; a slope far above 1 would mean the switching cost")
        print("  c_k itself grows with tau, which the decomposition does not assume.")

    # --- conditional-count and exceedance trends (regional criterion) ---
    print("\nREGIONAL CRITERION INPUTS (Section 6 of the theory document)")
    g = tab.dropna(subset=["D_star"]).groupby("tau").agg(
        conditional_options=("conditional", "sum"),
        mean_p_exceed=("p_exceed", "mean"))
    print(g.round(3).to_string())
    print("\n  Theory predicts the conditional count RISES and Pr(D > D*) FALLS as")
    print("  tau grows: a slower plant has more options it cannot profitably use,")
    print("  and a narrower band of disruptions worth responding to.")
    print("\nwrote data/tau_sweep_estimates.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--taus", default="12,18,24,30,36,48")
    ap.add_argument("--cats", default="D1,D3,D4,D8")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--path", default="control",
                    choices=["control", "topology", "crude"],
                    help="control: binary control inputs (do NOT traverse the "
                         "dryer). topology: compiler edge activation, which "
                         "does, and is the correct unit-slope test.")
    ap.add_argument("--cold", action="store_true",
                    help="use the cold-start commissioning contract")
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        analyze(); return

    taus = [float(t) for t in a.taus.split(",")]
    jobs = [(t, c, a.n, a.path, a.cold) for t in taus
            for c in a.cats.split(",")]
    print(f"{len(jobs)} cells (tau x category), {a.workers} workers, "
          f"{a.n} scenarios/cell")
    if a.workers == 1:
        for j in jobs:
            print(run_cell(j), flush=True)
    else:
        from multiprocessing import get_context
        with get_context("spawn").Pool(a.workers) as pool:
            for msg in pool.imap_unordered(run_cell, jobs):
                print(msg, flush=True)
    print("\nnow run: python scripts/tau_sweep.py --analyze")


if __name__ == "__main__":
    main()

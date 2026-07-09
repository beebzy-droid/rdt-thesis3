# RDT — Reactive Digital Twin (MS Thesis III, UP Diliman ChE)

Reactive Digital Twin with GNN-guided topology reconfiguration and MILP
optimization for resilient Philippine coconut processing complex operations
under supply chain disruption.

**Status: Week 1–5 infrastructure. All gates PASS.**

| Gate | Criterion | Measured |
|---|---|---|
| R1 operator-splitting vs analytical | rel. err < 1e-3 | ~1e-15 |
| Structural filter discrimination | valid ✓ / broken ✗ | correct |
| HiGHS MILP latency, K=50 | < 5 s | 4.7 ms |
| Determinism (CRN prerequisite) | bit-identical | True |

## Layout
- `rdt_core/graph.py` — process graph, structural feasibility filter
  (**§2.4.1 amendment**: scalar-incidence rank condition proven vacuous at the
  week-0 gate; degree/reachability filter implemented instead — see docstring)
- `rdt_core/icpc_graph.py` — ICPC G_max superstructure, single source of truth
  (|V|=25, 30 nominal + 10 candidate edges, seed exclusion pairs)
- `rdt_core/toy_flowsheet.py` — 3-unit analytical DAE (Risk R1 gate)
- `rdt_core/sim.py` — SimPy ⊕ CasADi operator-splitting driver
- `data/g_max.json` — frozen graph of record (v0.1.0-seed)
- `scripts/gate_r1.py` — reproduces every number above
- `tests/` — CI-enforced gate assertions

## Run
```
pip install -r requirements.txt pytest
python -m pytest tests/ -v
python scripts/gate_r1.py
```

## Integrity rules (lifecycle doc §9.2)
No fabricated/unverified data — [est.]/[verify] flags in code comments are
binding. No silent metric substitution — acceptance criteria are frozen;
changes are documented amendments.

## Reproducing results

Cross-platform entry point (no GNU make required):

    python scripts/reproduce.py          # rebuild screen + provenance + figures
    python -m pytest tests/ -q           # 34 gates

Convenience wrappers: `make <target>` (Linux/macOS) or `make.bat <target>`
(Windows) — targets: env, gpu, test, screen, provenance, figures, reproduce,
campaign. The GBT screen is rebuilt deterministically from its recipe; no model
binary is committed (sklearn-version portability). Full H4/H5 campaign:
`python scripts/campaign.py --cats D1,D3,D4,D8 --n 500 --workers 12`.

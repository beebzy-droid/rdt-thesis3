# Prior-Art Distinction: Ovalle et al. (2024) vs the Reactive Digital Twin

*Full-body read completed 2026-07-04 (32 pp, project file
`Process_resilience_or_supplychain_disruption_in_CPI_3.pdf`). This closes the
provisional first-page-only distinction flagged in `references.bib`. Verdict: the
two works do not overlap in contribution; the distinction is defensible on every
axis and is now empirically grounded in Ovalle's own problem statement and model.*

## Why this paper matters

Ovalle et al. (2024), from the Grossmann group at CMU with Dow co-authors, is the
nearest neighbour to this thesis by title: "Optimal Reactive Operation of General
Topology Supply Chain and Manufacturing Networks under Disruptions." A CCE or RESS
reviewer who knows this paper will look for an explicit distinction in the first
two pages of our Introduction. This document is the evidence base for that
paragraph.

## What Ovalle actually does (from its problem statement, not its title)

- **Object:** a multi-material **supply chain and manufacturing network** whose
  nodes are *suppliers, plants, warehouses, and customers* (their Figure 1), with
  arcs representing transportation modes between facilities.
- **Decisions:** shipment amounts and routes, plant production schedules, material
  acquisition, and **order management** (which orders to delay/renegotiate) per
  material per node per time period.
- **Method:** a **multiperiod mixed-integer linear program** minimizing the
  financial impact of a disruption. Discrete-time, linear. Verified by full-text
  probe: MILP/binary/continuous-variable language throughout; **zero continuous
  dynamics** (every apparent "ode" token is "node"/"model"/"code"; no
  differential equations, no transient model).
- **Time granularity:** operational horizon at daily/hourly resolution via time-
  period discretization (their emphasis is scalability under finer discretization).
- **What is given, not decided:** the physical supply-chain *design* is fixed;
  the paper optimizes *operation* "within the restrictions of the physical supply
  chain design." Topology is the arbitrary-but-**fixed** substrate over which
  flows are optimized, not a decision variable that is switched in response.

## What the RDT does that Ovalle does not

Axis-by-axis, grounded in Ovalle's text (left) against this work (right):

| Axis | Ovalle et al. 2024 | Reactive Digital Twin (this work) |
|---|---|---|
| **Network granularity** | Facilities as nodes; arcs are transport modes between sites | Unit operations, utilities, storage as nodes; edges are **material streams, unit routings, utility connections** inside one plant |
| **Topology role** | Fixed substrate; flows optimized over it | **Runtime decision variable**: edges activate/deactivate ($\Delta G$ operator), the plant is rewired mid-disruption |
| **Physics** | None; discrete-time linear flow/inventory balances | **Index-1 DAE** with reactor/dryer/evaporator dynamics, thermodynamic equilibria, utility pressure-flow; transient reachability checked |
| **Disruption sensing** | Disruption assumed known at model-build; no detector | **Online detection** (BOCPD + CUSUM) is inside the loop; onset is discovered, not given |
| **Decision engine** | Single monolithic MILP | **Layered loop**: detect -> learned GNN screen -> MILP -> DAE verify, recurrent |
| **Learning** | None (MILP only; "machine learning" appears once, as related-work context) | GNN surrogate screens a $10^9$ reconfiguration space; the screen's scaling limit is itself a reported result |
| **Real-time budget** | Daily/hourly operational horizon | Sub-second cycle (3.1 ms recompile, 4.7 ms MILP); designed for minutes-scale plant response |
| **Verification of action** | Feasibility within the LP | **Dynamic reachability**: does the transient physically reach the target state without violating a constraint |

## The one-sentence distinction (for the paper)

Ovalle optimizes *how to route flows and manage orders* across a **fixed
multi-facility supply-chain network** under a disruption, as a discrete-time MILP;
the RDT decides *how to physically rewire a single process plant* in real time,
coupling online detection, a learned screen, exact selection, and DAE-based
dynamic verification. Same two words ("reactive," "topology"); different object
(supply-chain network vs process plant), different granularity (facilities vs
streams/units/utilities), different physics (none vs index-1 DAE), and a different
machine (monolithic MILP vs recurrent detect-screen-select-verify loop).

## Fit note (journal-specific, not generic)

This distinction *strengthens* the CCE fit rather than threatening it. Ovalle is
itself CCE-adjacent (Grossmann/PSE community), which confirms the topic area is in
scope; and the RDT occupies the complementary niche the Grossmann paper explicitly
brackets out, namely the **plant-physics-level, real-time, dynamics-verified**
reconfiguration problem, as opposed to the **network-operational, discrete-time,
optimization-only** problem. Citing Ovalle as the closest neighbour and drawing
this line is exactly the move that reads as *specific command of the literature*
to a PSE reviewer, not generic gap-claiming.

## Residual honesty

Two constructs are genuinely shared and should be acknowledged, not hidden: both
use MILP as the exact-optimization layer, and both treat "arbitrary topology" as a
first-class modeling concern rather than assuming a feed-forward chain. The
distinction is not that the RDT invents these; it is that the RDT applies them at
plant-physics granularity inside a real-time sensing-and-verification loop, which
Ovalle neither attempts nor claims.

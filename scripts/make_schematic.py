"""scripts/make_schematic.py — Figure F0: the RDT architecture schematic.

The four-engine recurrent loop (detect -> screen -> select -> verify -> act),
drawn around the physical plant / DAE model at center, with the runtime-topology
graph as the shared data object. Publication style: flat fills, colorblind-safe,
grayscale-legible (distinct via position and label, not hue alone), vector PDF +
300 dpi PNG. Matches the F1-F9 palette. No external assets.

Usage: python scripts/make_schematic.py   ->  figures/F0_architecture.{png,pdf}
"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.patches import ConnectionStyle

FIG = pathlib.Path("figures"); FIG.mkdir(exist_ok=True)
# palette consistent with make_figures.py, plus neutral structure tones
COL = {"detect": "#0173b2", "screen": "#de8f05", "select": "#029e73",
       "verify": "#cc78bc", "plant": "#444444", "graph": "#7a7a7a",
       "edge": "#333333", "faded": "#e9e9e9"}
plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans"})


def box(ax, xy, w, h, title, lines, color):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.06",
                 linewidth=1.6, edgecolor=color, facecolor="white", zorder=3))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.34), w, 0.34,
                 boxstyle="round,pad=0.02,rounding_size=0.06",
                 linewidth=0, facecolor=color, alpha=0.16, zorder=3))
    ax.text(x + w / 2, y + h - 0.17, title, ha="center", va="center",
            fontsize=9.5, fontweight="bold", color=color, zorder=4)
    ax.text(x + w / 2, y + (h - 0.34) / 2, "\n".join(lines), ha="center",
            va="center", fontsize=7.4, color="#222222", zorder=4, linespacing=1.35)


def arrow(ax, p0, p1, color, rad=0.0, label=None, lpos=0.5, loff=(0, 0),
          style="-|>", lw=1.7, ls="-"):
    a = FancyArrowPatch(p0, p1, connectionstyle=f"arc3,rad={rad}",
                        arrowstyle=style, mutation_scale=13, linewidth=lw,
                        color=color, zorder=2, linestyle=ls)
    ax.add_patch(a)
    if label:
        mx = (1 - lpos) * p0[0] + lpos * p1[0] + loff[0]
        my = (1 - lpos) * p0[1] + lpos * p1[1] + loff[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=6.8,
                color=color, zorder=5,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))


fig, ax = plt.subplots(figsize=(8.2, 5.4))
ax.set_xlim(0, 10); ax.set_ylim(0, 6.6); ax.axis("off")

# --- central plant / DAE model + runtime-topology graph -------------------
cx, cy = 5.0, 3.3
ax.add_patch(Circle((cx, cy), 1.06, facecolor=COL["faded"],
                    edgecolor=COL["plant"], linewidth=1.6, zorder=1))
ax.text(cx, cy + 0.66, "Physical plant", ha="center", fontsize=8.2,
        color=COL["plant"], fontweight="bold")
ax.text(cx, cy + 0.40, "+ DAE twin", ha="center", fontsize=8.2,
        color=COL["plant"], fontweight="bold")
# a tiny runtime-topology graph glyph inside
gx, gy = cx, cy - 0.28
nodes = [(-0.42, 0.10), (0.0, 0.34), (0.42, 0.10), (-0.24, -0.30),
         (0.24, -0.30)]
edges = [(0, 1), (1, 2), (0, 3), (3, 4), (4, 2)]
for i, j in edges:
    ax.plot([gx + nodes[i][0], gx + nodes[j][0]],
            [gy + nodes[i][1], gy + nodes[j][1]],
            color=COL["graph"], lw=1.2, zorder=2)
# one "reconfigured" edge dashed in accent
ax.plot([gx + nodes[3][0], gx + nodes[4][0]], [gy + nodes[3][1], gy + nodes[4][1]],
        color=COL["select"], lw=2.0, ls=(0, (2, 1.5)), zorder=2)
for nx, ny in nodes:
    ax.add_patch(Circle((gx + nx, gy + ny), 0.062, facecolor="white",
                        edgecolor=COL["graph"], linewidth=1.1, zorder=3))
ax.text(cx, cy - 0.86, "topology G(t) = runtime data", ha="center",
        fontsize=6.6, style="italic", color=COL["graph"])

# --- four engine boxes around the loop ------------------------------------
bw, bh = 2.5, 1.28
detect = (0.25, 4.7)
screen = (7.25, 4.7)
select = (7.25, 0.62)
verify = (0.25, 0.62)
box(ax, detect, bw, bh, "1  DETECT",
    ["hybrid BOCPD + CUSUM", "run-length posterior", "fires on onset"], COL["detect"])
box(ax, screen, bw, bh, "2  SCREEN",
    ["GATv2 surrogate", "scores every candidate", "prunes 10\u2079 change space"], COL["screen"])
box(ax, select, bw, bh, "3  SELECT",
    ["MILP over candidates", "graph-derived constraints", "HiGHS, 4.7 ms"], COL["select"])
box(ax, verify, bw, bh, "4  VERIFY",
    ["index-1 DAE integration", "reachable + feasible?", "3.1 ms recompile"], COL["verify"])

# --- clockwise loop arrows through the center -----------------------------
# detect -> screen (top)
arrow(ax, (detect[0] + bw, detect[1] + bh / 2),
      (screen[0], screen[1] + bh / 2), COL["edge"], rad=-0.18,
      label="change detected", lpos=0.5, loff=(0, 0.28))
# screen -> select (right)
arrow(ax, (screen[0] + bw / 2, screen[1]),
      (select[0] + bw / 2, select[1] + bh), COL["edge"], rad=-0.18,
      label="candidate set", lpos=0.5, loff=(0.62, 0))
# select -> verify (bottom)
arrow(ax, (select[0], select[1] + bh / 2),
      (verify[0] + bw, verify[1] + bh / 2), COL["edge"], rad=-0.18,
      label="proposed \u0394G", lpos=0.5, loff=(0, -0.28))
# verify -> detect (left): the recurrence, emphasized
arrow(ax, (verify[0] + bw / 2, verify[1] + bh),
      (detect[0] + bw / 2, detect[1]), COL["edge"], rad=-0.18,
      label="apply \u0026 re-observe", lpos=0.5, loff=(-0.66, 0), lw=1.7)

# --- data exchange with the center (thin, into/out of plant) --------------
arrow(ax, (cx - 0.95, cy + 0.55), (detect[0] + bw - 0.35, detect[1] + 0.15),
      COL["detect"], rad=0.10, style="-|>", lw=1.0, ls=(0, (3, 2)))
arrow(ax, (screen[0] + 0.35, screen[1] + 0.15), (cx + 0.95, cy + 0.55),
      COL["screen"], rad=0.10, style="<|-", lw=1.0, ls=(0, (3, 2)))
arrow(ax, (cx + 0.95, cy - 0.55), (select[0] + 0.35, select[1] + bh - 0.15),
      COL["select"], rad=0.10, style="<|-", lw=1.0, ls=(0, (3, 2)))
arrow(ax, (verify[0] + bw - 0.35, verify[1] + bh - 0.15), (cx - 0.95, cy - 0.55),
      COL["verify"], rad=0.10, style="-|>", lw=1.0, ls=(0, (3, 2)))

# --- recurrence annotation -------------------------------------------------
ax.text(5.0, 6.36, "Reactive Digital Twin: the recurrent reconfiguration loop",
        ha="center", fontsize=10.5, fontweight="bold", color="#111111")
ax.text(5.0, 0.16,
        "every cycle re-decides as the disruption reveals itself  \u2022  "
        "solid: control flow   dashed: plant\u2013model data exchange",
        ha="center", fontsize=6.8, color="#555555")

for ext in ("png", "pdf"):
    fig.savefig(FIG / f"F0_architecture.{ext}", dpi=300, bbox_inches="tight")
plt.close(fig)
print("F0_architecture written to", FIG.resolve())

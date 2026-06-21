"""Render the van-facing curve with labelled reference points (A, B, C...).

These labels are our shared vocabulary for requesting tweaks: each is a
junction between the wire's underlying segments. Output: profile_labelled.png

Run: uv run python models/van_camera_mount/label_profile.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from build123d import *

HERE = Path(__file__).parent
van = import_svg(HERE / "sources" / "door_profile.svg")[0]

# Walk the edges in order from the hook tip (@0.0) to the bottom of the run.
import math
def dist(a, b):
    return math.hypot(a.X - b.X, a.Y - b.Y)

remaining = list(van.edges())
cur = van.position_at(0.0)
ordered = []
while remaining:
    best, brev, bd = None, False, 1e9
    for e in remaining:
        if dist(e.position_at(0), cur) < bd:
            bd, best, brev = dist(e.position_at(0), cur), e, False
        if dist(e.position_at(1), cur) < bd:
            bd, best, brev = dist(e.position_at(1), cur), e, True
    ordered.append((best, brev))
    cur = best.position_at(0) if brev else best.position_at(1)
    remaining.remove(best)

# Junction points = start of each segment + final end point.
pts = []
for e, rev in ordered:
    pts.append(e.position_at(1 if rev else 0))
pts.append(ordered[-1][0].position_at(0 if ordered[-1][1] else 1))
labels = [chr(ord("A") + i) for i in range(len(pts))]

# Dense polyline of the actual curve for the plot.
N = 600
xs = [van.position_at(i / N).X for i in range(N + 1)]
ys = [van.position_at(i / N).Y for i in range(N + 1)]

def draw(ax, label_pts, off=7):
    ax.plot(xs, ys, "-", color="#1565c0", lw=2, zorder=1)
    ax.scatter([p.X for p in pts], [p.Y for p in pts],
               color="#c62828", s=40, zorder=3)
    cx = sum(p.X for p in pts) / len(pts)
    cy = sum(p.Y for p in pts) / len(pts)
    for lab, p in zip(labels, pts):
        if lab not in label_pts:
            continue
        vx, vy = p.X - cx, p.Y - cy
        n = math.hypot(vx, vy) or 1
        ax.annotate(
            f"{lab}\n({p.X:.1f}, {p.Y:.1f})",
            (p.X, p.Y), (p.X + vx / n * off, p.Y + vy / n * off),
            fontsize=9, fontweight="bold", color="#c62828",
            ha="center", va="center",
            arrowprops=dict(arrowstyle="-", color="#c62828", lw=0.6),
        )
    ax.set_aspect("equal")
    ax.grid(True, ls=":", alpha=0.5)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")

fig, (axm, axz) = plt.subplots(1, 2, figsize=(12, 11),
                               gridspec_kw={"width_ratios": [2, 1]})
# Main view: label the well-separated points only (F, G, H, and the curl as a group).
draw(axm, {"F", "G", "H"})
axm.annotate("hook / curl\n(A–E, see zoom →)", (33, 117), (20, 100),
             fontsize=10, fontweight="bold", color="#c62828", ha="center",
             arrowprops=dict(arrowstyle="->", color="#c62828"))
axm.set_title("Van-facing profile — reference points")
# Zoom: the curl, all of A–E.
draw(axz, {"A", "B", "C", "D", "E"}, off=2.5)
axz.set_xlim(27, 36)
axz.set_ylim(112, 122)
axz.set_title("Hook / rolled-lip curl (zoom)")
fig.tight_layout()
out = HERE / "profile_labelled.png"
fig.savefig(out, dpi=130)
print("wrote", out)
for lab, p in zip(labels, pts):
    print(f"  {lab}: ({p.X:6.2f}, {p.Y:6.2f})")

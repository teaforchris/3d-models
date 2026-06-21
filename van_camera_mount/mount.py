"""Van reversing-camera mount — model 1.

Contact face = the fit-validated van-door curve (door_profile.svg, hook at top).
The raw curve fits the metal; print-testing showed two small rests-gaps that we
correct with the parametric tweaks below (see profile_labelled.png for points
A-H). Everything tunable lives in the PARAMETERS block.

Run: uv run python van_camera_mount/mount.py            (preview only)
     uv run python van_camera_mount/mount.py --export  (+ datetimed STL)
Live preview: open the "OCP CAD Viewer" panel first (hot-reloads on save).
"""
import math
import sys
from datetime import datetime
from pathlib import Path

from build123d import *
from ocp_vscode import show

HERE = Path(__file__).parent
SVG = HERE / "sources" / "door_profile.svg"
OUTPUTS = HERE / "outputs"

# ---- PARAMETERS (everything tunable lives here) ----
wall          = 3.0        # mm  wall thickness, added to the NON-van side
extrude_width = 3.0        # mm  mount width (Z); 3 = thin print-test slice, 50 = full
offset_side   = Side.RIGHT # 3 mm on the OUTSIDE of the curl, keeps the hook open

# Profile tweaks (override the validated curve to close rests-gaps found on the van):
#   ef_extend: lengthen the E->F sweep along its natural tangent, carrying the
#              F-G-H tail rigidly -> seats point F (closes the F..mid-FE air gap).
#   fg_extend: continue the F-G arc along its own curvature past G; the G-H leg
#              follows the arc tangent (no kink at G) -> swings point H onto the
#              van. +ve moves H toward the door. ~0.35 mm of arc ~= ~1 mm at H.
ef_extend     = 0.5        # mm
fg_extend     = 0.35       # mm


def _ordered_edges(wire):
    """Edges of `wire` oriented and ordered along the walk from position_at(0)."""
    def dist(a, b):
        return math.hypot(a.X - b.X, a.Y - b.Y)
    rem, cur, out = list(wire.edges()), wire.position_at(0.0), []
    while rem:
        best, brev, bd = None, False, 1e9
        for e in rem:
            if dist(e.position_at(0), cur) < bd:
                bd, best, brev = dist(e.position_at(0), cur), e, False
            if dist(e.position_at(1), cur) < bd:
                bd, best, brev = dist(e.position_at(1), cur), e, True
        out.append(best.reversed() if brev else best)
        cur = out[-1].position_at(1)
        rem.remove(best)
    return out


def _fit_circle(edge):
    """Centre + radius of the circle through edge endpoints and midpoint."""
    a, b, c = edge.position_at(0), edge.position_at(0.5), edge.position_at(1)
    ax, ay, bx, by, cx, cy = a.X, a.Y, b.X, b.Y, c.X, c.Y
    da = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay)
          + (cx * cx + cy * cy) * (ay - by)) / da
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx)
          + (cx * cx + cy * cy) * (bx - ax)) / da
    return Vector(ux, uy, 0), math.hypot(ax - ux, ay - uy)


def build_contact_wire(ef_extend=ef_extend, fg_extend=fg_extend):
    """The van-contact curve with the seat tweaks applied. Hook (A-E) untouched."""
    edges = _ordered_edges(import_svg(SVG)[0])
    hook, sweep, arc, leg = edges[0:4], edges[4], edges[5], edges[6]

    # 1) ef_extend: stub the sweep along its end tangent; translate the tail.
    F = sweep.position_at(1)
    p = sweep.position_at(1 - 1e-4)
    tF = (F - p)
    tF = tF / tF.length
    v1 = tF * ef_extend
    stub = Line(F, F + v1)
    arc_t = arc.translate(v1)

    # 2) fg_extend: continue the (translated) arc past G along its curvature.
    O, R = _fit_circle(arc_t)
    G_t = arc_t.position_at(1)
    thG = math.atan2(G_t.Y - O.Y, G_t.X - O.X)
    dth = fg_extend / R                       # +ve = anticlockwise = toward van
    ext = CenterArc(center=O, radius=R,
                    start_angle=math.degrees(thG), arc_size=math.degrees(dth))
    Gp = O + Vector(R * math.cos(thG + dth), R * math.sin(thG + dth), 0)
    # leg follows the arc tangent: translate, rotate by dth, reseat onto G'.
    leg_f = (leg.translate(v1)
                .rotate(Axis((G_t.X, G_t.Y, 0), (0, 0, 1)), math.degrees(dth))
                .translate(Gp - G_t))

    return Wire(hook + [sweep, stub, arc_t, ext, leg_f])


van = build_contact_wire()
band = offset(van, amount=wall, side=offset_side, closed=True)
section = make_face(band)
mount = extrude(section, amount=extrude_width)

if __name__ == "__main__":
    bb = mount.bounding_box()
    print("solid valid:", mount.is_valid)
    print("solid volume (mm^3):", round(mount.volume, 1))
    print("bbox size (mm):", bb.size)
    show(mount)
    if "--export" in sys.argv:
        OUTPUTS.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        stl = OUTPUTS / f"mount_w{extrude_width:g}_{stamp}.stl"
        export_stl(mount, str(stl))
        print("exported", stl.relative_to(HERE.parent))

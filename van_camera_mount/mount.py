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
extrude_width = 50.0       # mm  mount width (Z); 3 = thin print-test slice, 50 = full
# (the offset side is auto-chosen so the wall lands OUTSIDE the curl regardless of
#  wire winding — see _offset_outward; a hardcoded Side once silently filled the
#  hook throat after a wire rebuild, so we pick it geometrically and assert.)

# Profile seat tweaks. VALIDATED & LOCKED against the real van — fit is PERFECT.
# Treat as inviolable as the SVG; do not change without a new physical fit test.
#   ef_extend: lengthen the E->F sweep along its natural tangent, carrying the
#              F-G-H tail rigidly -> seats point F (closes the F..mid-FE air gap).
#   fg_extend: continue the F-G arc along its own curvature past G; the G-H leg
#              follows the arc tangent (no kink at G) -> swings point H onto the
#              van. +ve moves H toward the door. ~0.35 mm of arc ~= ~1 mm at H.
ef_extend     = 0.5        # mm  LOCKED
fg_extend     = 0.35       # mm  LOCKED

# ---- MAGNETS (recessed from the BACK; van-side skin stays one continuous surface) ----
# Pockets open on the outside/back and are blind toward the van, leaving a thin
# skin so the contact face never breaks (no steel/paint contamination). The G->H
# wall is locally thickened to back_wall to host them. Magnet nominal 6x3 mm;
# refine magnet_dia/press_fit once measured with calipers.
magnet_dia    = 6.0        # mm  magnet diameter (nominal)
magnet_depth  = 3.0        # mm  magnet thickness; pocket depth = this (flush at back)
press_fit     = 0.1        # mm  pocket dia = magnet_dia - press_fit (interference)
skin          = 0.8        # mm  van-side membrane over the magnet (~4 layers @0.2)
back_wall     = skin + magnet_depth        # mm  G->H wall thickness (derived = 3.8)
magnet_rows   = (11.0, 26.0)               # mm  positions along G->H, from G
magnet_cols   = (9.0, 25.0, 41.0)          # mm  positions across width (Z)

# ---- MATERIAL REDUCTION ----
# The hook's only job is to grip the door lip, so the hook + E->F sweep don't
# need full width: keep two arms at the edges and cut the middle away (above F).
arm_width     = 5.0        # mm  width of each hook arm left at the edges
arm_fillet    = 1.5        # mm  fillet at each arm root (relieves the stress riser)

# ---- CAMERA MOUNT BRACKETS ----
# Two arms projecting rearward off the boss/back face; the camera bolts between
# them with an M2 bolt (axis along the width). Spec: 13 mm inner gap, 3 mm thick
# arms, hole centres 20 mm clear of the boss back face.
bracket_gap   = 13.0       # mm  inner distance between the two arms (camera width)
bracket_thick = 3.0        # mm  arm thickness (along width Z)
bolt_clear    = 20.0       # mm  M2 hole centre distance from the boss back face
m2_clear_dia  = 2.4        # mm  M2 bolt clearance hole
hole_wall     = 2.0        # mm  material around the hole (sets tip radius & arm width)
bracket_base_fillet = 6.0  # mm  exaggerated base fillet, in the XY (profile) plane only
bracket_s     = None       # mm  position along G->H from G; None = mid-boss


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


def _offset_outward(wire, wall):
    """Offset `wire` into a wall-thick band on the OUTSIDE of the curl.

    The correct side depends on the wire's winding (which a rebuild can flip), so
    instead of hardcoding Side.LEFT/RIGHT we build both and keep the one that adds
    material above the curl crown — i.e. keeps the hook throat open. Asserts the
    hook survived so a wrong-side offset can never silently ship to a print again.
    """
    crown = max(v.Y for v in wire.vertices())            # top of the rolled-lip curl
    faces = [make_face(offset(wire, amount=wall, side=s, closed=True))
             for s in (Side.LEFT, Side.RIGHT)]
    outward = max(faces, key=lambda f: f.bounding_box().max.Y)
    clearance = outward.bounding_box().max.Y - crown
    assert clearance > 0.5 * wall, (
        f"offset collapsed the hook: wall only {clearance:.2f} mm above the curl "
        f"crown (expected ~{wall:.1f}). Both sides filled the throat?")
    return outward


def add_magnets(part, wire):
    """Thicken the G->H wall to back_wall and recess the magnet pockets.

    Pockets open on the back (outside) and stop `skin` short of the van face, so
    the contact surface stays one continuous skin of plastic. The boss adds the
    extra wall on the outside only — the validated van face is untouched.
    """
    leg = _ordered_edges(wire)[-1]                 # the G->H back-face leg
    G, H = leg.position_at(0), leg.position_at(1)
    d = H - G
    Lgh = d.length
    d = d / Lgh
    n = Vector(d.Y, -d.X, 0)                        # outward normal (into plastic/back)

    # Boss: raise the G->H wall from `wall` to `back_wall`, full width, ends inset.
    inset = 3.0
    lo = wall - 0.4                                 # overlap into existing wall to fuse cleanly
    centre = G + d * (Lgh / 2) + n * ((lo + back_wall) / 2)
    centre = Vector(centre.X, centre.Y, extrude_width / 2)
    plane = Plane(origin=centre, x_dir=d, z_dir=(0, 0, 1))
    part = part + plane * Box(Lgh - 2 * inset, back_wall - lo, extrude_width)

    # Pockets: cylinders drilled from the back toward the van, floor at `skin`.
    over = 0.6                                      # break cleanly through the back face
    pcd = skin + (magnet_depth + over) / 2          # pocket centre dist from van face
    r = (magnet_dia - press_fit) / 2
    for s in magnet_rows:
        for z in magnet_cols:
            c = G + d * s + n * pcd
            c = Vector(c.X, c.Y, z)
            part = part - Plane(origin=c, z_dir=n) * Cylinder(radius=r,
                                                              height=magnet_depth + over)
    return part


def cut_arms(part, wire):
    """Remove the middle of the hook + E->F sweep, leaving an arm at each edge.

    Everything above F (the bend) loses its middle width; the lower FG arc + GH
    plate region stays full width. Two `arm_width` hook arms remain at Z edges.
    """
    sweep = max(_ordered_edges(wire), key=lambda e: e.length)   # the long E->F sweep
    cut_y = min(sweep.position_at(0).Y, sweep.position_at(1).Y)  # F = its lower end
    bb = part.bounding_box()
    box = Box(bb.size.X + 2, (bb.max.Y + 1) - cut_y, extrude_width - 2 * arm_width)
    centre = ((bb.min.X + bb.max.X) / 2, (cut_y + bb.max.Y + 1) / 2, extrude_width / 2)
    part = part - Pos(*centre) * box

    # Fillet the re-entrant edge at each arm root (Y=cut_y, Z at the arm boundary).
    if arm_fillet > 0:
        def midz(e):
            return (e.position_at(0).Z + e.position_at(1).Z) / 2
        roots = [e for e in part.edges()
                 if abs(e.position_at(0).Y - cut_y) < 0.25
                 and abs(e.position_at(1).Y - cut_y) < 0.25
                 and (abs(midz(e) - arm_width) < 0.25
                      or abs(midz(e) - (extrude_width - arm_width)) < 0.25)]
        if roots:
            part = fillet(roots, radius=arm_fillet)
    return part


def _bracket_arm(base, d, n, zc, hole_n, tip_r, root_n):
    """One rounded-tongue arm at width-position zc, before fusing to the body."""
    # Shaft (root -> hole centre) + semicircular tip cap concentric with the hole.
    shaft_c = base + n * ((root_n + hole_n) / 2)
    shaft_pl = Plane(origin=Vector(shaft_c.X, shaft_c.Y, zc), x_dir=n, z_dir=(0, 0, 1))
    shaft = shaft_pl * Box(hole_n - root_n, 2 * tip_r, bracket_thick)
    tip_c = base + n * hole_n
    tip = Plane(origin=Vector(tip_c.X, tip_c.Y, zc), z_dir=(0, 0, 1)) * Cylinder(
        radius=tip_r, height=bracket_thick)
    return shaft + tip                              # straight sides, curved (tongue) top


def add_brackets(part, wire):
    """Two rounded-tongue arms with M2 holes — the camera bolts between them."""
    leg = _ordered_edges(wire)[-1]
    G, H = leg.position_at(0), leg.position_at(1)
    d = H - G
    Lgh = d.length
    d = d / Lgh
    n = Vector(d.Y, -d.X, 0)                         # outward (rearward) normal
    s = bracket_s if bracket_s is not None else Lgh / 2
    base = G + d * s                                 # attach point on the back face

    tip_r = m2_clear_dia / 2 + hole_wall             # 2 mm of material around the hole
    hole_n = back_wall + bolt_clear                  # hole centre, 20 mm off the boss
    root_n = wall - 1.0                              # embed into the wall so it fuses
    z_centres = (extrude_width / 2 - (bracket_gap + bracket_thick) / 2,
                 extrude_width / 2 + (bracket_gap + bracket_thick) / 2)
    for zc in z_centres:
        part = part + _bracket_arm(base, d, n, zc, hole_n, tip_r, root_n)

    # Exaggerated base fillet, in the XY (profile) plane only: the root edges that
    # run along Z (the arm's two sides), where the arm sides meet the boss face.
    if bracket_base_fillet > 0:
        def ncoord(p):
            return (Vector(p.X, p.Y, 0) - Vector(G.X, G.Y, 0)).dot(n)
        def dcoord(p):
            return (Vector(p.X, p.Y, 0) - Vector(G.X, G.Y, 0)).dot(d)
        roots = []
        for e in part.edges():
            t = e.position_at(1) - e.position_at(0)
            along_z = abs(t.Z) / (t.length or 1) > 0.9
            m = (e.position_at(0) + e.position_at(1)) * 0.5
            near_boss = abs(ncoord(m) - back_wall) < 0.7
            near_arm = abs(dcoord(m) - s) < tip_r + 0.5 and any(
                abs(m.Z - zc) < bracket_thick / 2 + 0.3 for zc in z_centres)
            if along_z and near_boss and near_arm:
                roots.append(e)
        if roots:
            part = fillet(roots, bracket_base_fillet)

    # M2 clearance hole through both arms (axis along Z), 20 mm off the boss face.
    hc = base + n * hole_n
    hc = Vector(hc.X, hc.Y, extrude_width / 2)
    part = part - Plane(origin=hc, z_dir=(0, 0, 1)) * Cylinder(
        radius=m2_clear_dia / 2, height=extrude_width + 2)
    return part


van = build_contact_wire()
section = _offset_outward(van, wall)
mount = extrude(section, amount=extrude_width)
mount = add_magnets(mount, van)
mount = cut_arms(mount, van)
mount = add_brackets(mount, van)

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

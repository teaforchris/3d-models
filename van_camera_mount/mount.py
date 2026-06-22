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
wall          = 3.8        # mm  wall thickness (NON-van side); uniform = back_wall for strength
extrude_width = 45.0       # mm  baseplate width (Z). DATUM = the RIGHT edge (max Z =
                           #     the door edge); fit measurements run negative leftward.
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
boss_inset    = 0.0        # mm  boss top at G (as high as the leg goes before the curve)
magnet_top_gap = 3.0       # mm  boss top edge -> top of the top magnet hole
pocket_radius = (magnet_dia - press_fit) / 2
row_spacing   = 15.0       # mm  spacing between the two magnet rows
_row1         = boss_inset + magnet_top_gap + pocket_radius   # top row anchored to the boss top
magnet_rows   = (_row1, _row1 + row_spacing)   # along G->H; whole group rides magnet_top_gap
mag_edge      = pocket_radius + 3.0            # 3 mm wall holding the outer magnets in
magnet_cols   = (mag_edge, extrude_width / 2, extrude_width - mag_edge)  # derived: cinch to width
# Extra magnets in the hook (over the door's rolled top), recessed from the outer
# up-facing side to pull the top down. Rows are fractions along the E->F sweep.
hook_magnet_rows = (0.1, 0.5, 0.85)         # fractions along the sweep (E=0 .. F=1)
hook_magnet_cols = (6.0, 16.0, 26.0)        # mm  Z across the solid hook

# ---- MATERIAL REDUCTION / HOOK ARMS ----
# The hook only locates on the door lip, so it needn't be full width OR at the
# plate edges: above F we keep just the hook bands listed here and cut the rest.
# Each entry is (Z centre, width). DATUM = right edge (extrude_width); a fit offset
# of -16 mm from the door edge => Z = extrude_width - 16.
arm_width     = 5.0        # mm  default hook-arm width
arm_fillet    = 1.5        # mm  fillet at each arm root (relieves the stress riser)
# Trim the dead wedge of plate to the RIGHT of the right arm (door-edge side),
# above the boss top, so the right arm's right face runs flush down to the boss.
wedge_fillet  = 3.0        # mm  fillet on the inside corner of that L-cut
hook_arms     = [(extrude_width - 16.0, arm_width),   # RIGHT hook: -16 mm off the door edge
                 (arm_width / 2, arm_width)]           # LEFT hook: flush with the plate's left edge
# Below the bottom magnet row the plate does nothing, so trim it off there.
tail_keep     = magnet_dia / 2 + 2.0   # mm  plate kept below the bottom magnet row
plate_corner  = 3.0        # mm  round the plate's outer corners (bottom L/R, top R)

# ---- CAMERA MOUNT BRACKETS ----
# Two arms projecting rearward off the boss/back face; the camera bolts between
# them with an M2 bolt (axis along the width). Spec: 14 mm inner gap, 3 mm thick
# arms, hole centres 20 mm clear of the boss back face.
bracket_gap   = 14.0       # mm  inner distance between the two arms (camera width)
bracket_thick = 3.0        # mm  arm thickness (along width Z)
bolt_clear    = 20.0       # mm  M2 hole centre distance from the boss back face
m2_clear_dia  = 2.4        # mm  M2 bolt clearance hole
hole_wall     = 2.0        # mm  material around the hole (sets tip radius & arm width)
bracket_base_fillet = 6.0  # mm  exaggerated base fillet, in the XY (profile) plane only
bracket_tip_r = m2_clear_dia / 2 + hole_wall    # tongue tip radius (2 mm wall around the hole)
bracket_s     = boss_inset + bracket_tip_r      # mm  along G->H: top face flush with the boss top (G)
# Top gusset (tension side): a buttress sweeping from the bracket up into the arc,
# since the flush top has no edge to fillet. Tunable shape:
gusset_reach  = bracket_base_fillet   # mm  reach OUT along the bracket = the bottom fillet radius
gusset_rise   = 8.0        # mm  how far UP the arc (above G) the gusset blends to (kept where the
                           #     body's outer surface is still outside gusset_embed, so it tucks in)
gusset_embed  = 1.0        # mm  wall-side sunk to this n (behind the contact face, inside the
                           #     back surface) so the union trims it flush to the curved outside
gusset_concavity = 0.25    # 0..1  how far the outer edge bows toward the corner (concave fillet);
                           #       >~0.3 bows so far it grazes the curved body and won't fuse


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
    inset = boss_inset
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


def add_outer_taper(part, wire):
    """Reshape the F->G outer surface so it flows flush into the boss (no shelf).

    Instead of a constant 3 mm offset that leaves a step where it meets the 3.8 mm
    boss, the wall thickness grows from `wall` at F to `back_wall` at G. Built as a
    tapered shell over the arc only (the validated offset elsewhere is untouched);
    the outer face follows the van offset, so it's a smooth new arc, not a blade.
    """
    edges = _ordered_edges(wire)
    sweep_i = max(range(len(edges)), key=lambda i: edges[i].length)
    leg_i = len(edges) - 1
    fg = list(range(sweep_i + 1, leg_i))
    fg_total = sum(edges[i].length for i in fg)
    lo = wall - 0.4                                 # inner sunk into the wall to fuse
    inner, outer, acc = [], [], 0.0
    for ei in fg:
        e = edges[ei]
        for j in range(19):
            u = j / 18
            p = e.position_at(u)
            tg = e.tangent_at(u)
            rn = Vector(tg.Y, -tg.X, 0)             # outward (right) normal
            t = wall + (back_wall - wall) * ((acc + u * e.length) / fg_total)
            inner.append(p + rn * lo)
            outer.append(p + rn * t)
        acc += e.length

    def dedup(seq):
        out = [seq[0]]
        for q in seq[1:]:
            if (q - out[-1]).length > 1e-4:
                out.append(q)
        return out

    inner, outer = dedup(inner), dedup(outer)
    face = make_face([Spline(*inner), Line(inner[-1], outer[-1]),
                      Spline(*outer), Line(outer[0], inner[0])])
    shell = extrude(face, amount=extrude_width)
    return (part + shell.translate((0, 0, -shell.bounding_box().min.Z))).clean()


def add_hook_magnets(part, wire):
    """Recess magnets into the hook (over the door's rolled top), from the outer
    up-facing side, blind toward the contact face — pulls the top down."""
    sweep = max(_ordered_edges(wire), key=lambda e: e.length)
    r = (magnet_dia - press_fit) / 2
    over = 0.6
    pcd = skin + (magnet_depth + over) / 2
    for u in hook_magnet_rows:
        p = sweep.position_at(u)
        tg = sweep.tangent_at(u)
        rn = Vector(tg.Y, -tg.X, 0)                 # outward (non-van) normal
        for z in hook_magnet_cols:
            c = p + rn * pcd
            c = Vector(c.X, c.Y, z)
            part = part - Plane(origin=c, z_dir=rn) * Cylinder(
                radius=r, height=magnet_depth + over)
    return part


def cut_arms(part, wire):
    """Above F, keep ONE solid hook band spanning the listed arms; cut the rest.

    The hook is solid from the leftmost arm's edge to the rightmost arm's edge
    (for holding strength), with everything beyond the right arm still removed for
    tail-light clearance. The lower FG arc + GH plate stays full width.
    """
    sweep = max(_ordered_edges(wire), key=lambda e: e.length)   # the long E->F sweep
    cut_y = min(sweep.position_at(0).Y, sweep.position_at(1).Y)  # F = its lower end
    bb = part.bounding_box()
    cx = (bb.min.X + bb.max.X) / 2
    cy = (cut_y + bb.max.Y + 1) / 2
    dx, dy = bb.size.X + 2, (bb.max.Y + 1) - cut_y
    above = Pos(cx, cy, extrude_width / 2) * Box(dx, dy, extrude_width + 4)
    left = min(zc - w / 2 for zc, w in hook_arms)               # solid across the arms' span
    right = max(zc + w / 2 for zc, w in hook_arms)
    band = Pos(cx, cy, (left + right) / 2) * Box(dx, dy, right - left)
    part = part - (above - band)                 # remove above-F material outside the span

    # Fillet the solid hook's root edges (Y=cut_y, at its two Z boundaries).
    if arm_fillet > 0:
        edges_z = [left, right]
        def midz(e):
            return (e.position_at(0).Z + e.position_at(1).Z) / 2
        roots = [e for e in part.edges()
                 if abs(e.position_at(0).Y - cut_y) < 0.25
                 and abs(e.position_at(1).Y - cut_y) < 0.25
                 and any(abs(midz(e) - z) < 0.25 for z in edges_z)]
        for r in (arm_fillet, 1.0, 0.6, 0.3):       # back off if the local faces are tight
            if not roots:
                break
            try:
                part = fillet(roots, radius=r)
                break
            except Exception:
                continue
    return part


def cut_right_wedge(part, wire):
    """L-cut the dead plate to the right of the right arm, above the boss top.

    Flush down the right arm's right face to the boss top, then in along the boss
    top to the door edge; the inside corner is filleted. The magnet plate below
    the boss top stays full width (keeps the right magnet column).
    """
    leg = _ordered_edges(wire)[-1]
    G, H = leg.position_at(0), leg.position_at(1)
    d = H - G
    d = d / d.length
    right_z = max(zc + w / 2 for zc, w in hook_arms)    # right face of the rightmost arm
    boss_top_s = boss_inset                              # boss top along the leg

    # Wedge = {Z > right arm's right face} AND {above the boss top, measured ALONG
    # the leg} — so the "inward" cut follows the slanted boss-top edge (no triangle).
    bb = part.bounding_box()
    cz = (right_z + bb.max.Z + 1) / 2
    base = G + d * (boss_top_s - 80 / 2)                 # box sits on the -d (toward F) side
    plane = Plane(origin=Vector(base.X, base.Y, cz), x_dir=d, z_dir=(0, 0, 1))
    part = part - plane * Box(80, 120, (bb.max.Z + 1) - right_z)
    return part


def add_plate_corners(part, wire):
    """Round the magnet plate's outer corners (bottom-left/right, top-right)."""
    if plate_corner <= 0:
        return part
    leg = _ordered_edges(wire)[-1]
    G, H = leg.position_at(0), leg.position_at(1)
    d = H - G
    d = d / d.length
    n = Vector(d.Y, -d.X, 0)
    s_tail = max(magnet_rows) + tail_keep
    W = extrude_width

    def s_of(q):
        return (Vector(q.X, q.Y, 0) - Vector(G.X, G.Y, 0)).dot(d)

    sel = []
    for zc, sc in ((0.0, s_tail), (W, s_tail), (W, 0.0)):   # bL, bR, topR
        for e in part.edges():
            t = e.position_at(1) - e.position_at(0)
            L = t.length
            if L < 1e-6 or abs((t.X * n.X + t.Y * n.Y) / L) <= 0.8:
                continue            # keep only edges running across the wall (along n)
            m = (e.position_at(0) + e.position_at(1)) * 0.5
            if abs(m.Z - zc) < 1.5 and abs(s_of(m) - sc) < 1.5:
                sel.append(e)
    for r in (plate_corner, 2.5, 2.0, 1.5):
        if not sel:
            break
        try:
            part = fillet(sel, r)
            break
        except Exception:
            continue
    return part


def add_wedge_fillet(part, wire):
    """Explicit fillet in the L-cut's re-entrant corner (OCC won't fillet it at G).

    The corner is at (Z = right arm edge, s = boss top), running across the wall.
    We union a quarter-round (box minus cylinder) that rounds the sharp inside
    corner for strength, overlapping the adjacent faces so it fuses cleanly.
    """
    if wedge_fillet <= 0:
        return part
    leg = _ordered_edges(wire)[-1]
    G, H = leg.position_at(0), leg.position_at(1)
    d = H - G
    d = d / d.length
    n = Vector(d.Y, -d.X, 0)
    R = wedge_fillet
    right_z = max(zc + w / 2 for zc, w in hook_arms)
    s0 = boss_inset                                     # boss top along the leg
    ov = 0.5                                            # overlap into the adjacent faces

    # Box over the notch corner (s in [s0-R, s0+ov], Z in [right_z-ov, right_z+R]),
    # spanning the wall thickness in n; minus a cylinder to leave the concave round.
    bc = G + d * (s0 + (-R + ov) / 2) + n * (back_wall / 2)
    box = Plane(origin=Vector(bc.X, bc.Y, right_z + (R - ov) / 2),
                x_dir=d, z_dir=(0, 0, 1)) * Box(R + ov, back_wall, R + ov)
    cc = G + d * (s0 - R) + n * (back_wall / 2)
    cyl = Plane(origin=Vector(cc.X, cc.Y, right_z + R), z_dir=n) * Cylinder(
        radius=R, height=back_wall + 2)
    return (part + (box - cyl)).clean()


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

    tip_r = bracket_tip_r                            # 2 mm of material around the hole
    hole_n = back_wall + bolt_clear                  # hole centre, 20 mm off the boss
    root_n = wall - 1.0                              # embed into the wall so it fuses
    # Anchor the pair so the right bracket's outer face is flush with the right
    # arm's right edge (no overhang past the mount edge), camera centreline follows.
    right_edge = max(zc + w / 2 for zc, w in hook_arms)
    z_right = right_edge - bracket_thick / 2
    z_centres = (z_right - (bracket_gap + bracket_thick), z_right)
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
            # bottom edge only (dcoord > s); the top is at the boss/taper junction
            # and filleting it together with the bottom fails at every radius.
            near_arm = dcoord(m) > s and abs(dcoord(m) - s) < tip_r + 0.5 and any(
                abs(m.Z - zc) < bracket_thick / 2 + 0.3 for zc in z_centres)
            if along_z and near_boss and near_arm:
                roots.append(e)
        for r in (bracket_base_fillet, 4.0, 3.0, 2.0):
            if not roots:
                break
            try:
                part = fillet(roots, r)
                break
            except Exception:
                continue

    # M2 clearance hole through both arms (axis along Z), 20 mm off the boss face.
    hc = base + n * hole_n
    hc = Vector(hc.X, hc.Y, extrude_width / 2)
    part = part - Plane(origin=hc, z_dir=(0, 0, 1)) * Cylinder(
        radius=m2_clear_dia / 2, height=extrude_width + 2)
    return part


def cut_tail(part, wire):
    """Trim the plate off just below the bottom magnet row (dead material)."""
    leg = _ordered_edges(wire)[-1]
    G, H = leg.position_at(0), leg.position_at(1)
    d = H - G
    d = d / d.length
    s_cut = max(magnet_rows) + tail_keep
    centre = G + d * (s_cut + 20)                    # box reaches H-ward from the cut
    plane = Plane(origin=Vector(centre.X, centre.Y, extrude_width / 2),
                  x_dir=d, z_dir=(0, 0, 1))
    return part - plane * Box(40, 60, extrude_width + 4)


def add_top_gussets(part, wire):
    """Buttress on the tension (top) side of each bracket, sweeping into the arc.

    The bracket top is flush with the boss top (no edge to fillet), so we add an
    explicit gusset: a triangle in the bending (XY) plane from the bracket, up the
    arc wall above G, spanning the bracket thickness.
    """
    leg = _ordered_edges(wire)[-1]
    G, H = leg.position_at(0), leg.position_at(1)
    d = H - G
    d = d / d.length
    n = Vector(d.Y, -d.X, 0)
    right_edge = max(zc + w / 2 for zc, w in hook_arms)
    z_right = right_edge - bracket_thick / 2
    z_centres = (z_right - (bracket_gap + bracket_thick), z_right)
    Pc = G + n * gusset_embed                       # sunk into the wall at s=0
    Pb = G + n * (back_wall + gusset_reach)         # out along the bracket top
    Pw = G - d * gusset_rise + n * gusset_embed     # sunk into the wall, up the arc above G
    mid = (Pb + Pw) * 0.5
    Marc = mid + (Pc - mid) * gusset_concavity      # bow the outer edge toward the corner
    for zc in z_centres:
        prof = make_face([Line((Pc.X, Pc.Y), (Pb.X, Pb.Y)),
                          ThreePointArc((Pb.X, Pb.Y), (Marc.X, Marc.Y), (Pw.X, Pw.Y)),
                          Line((Pw.X, Pw.Y), (Pc.X, Pc.Y))])
        part = (part + extrude(prof, amount=bracket_thick).translate(
            (0, 0, zc - bracket_thick / 2))).clean()   # clean() merges the tangent sliver
    return part


van = build_contact_wire()
section = _offset_outward(van, wall)
mount = extrude(section, amount=extrude_width)
mount = add_magnets(mount, van)
mount = cut_arms(mount, van)
mount = add_hook_magnets(mount, van)
mount = cut_tail(mount, van)
mount = cut_right_wedge(mount, van)
mount = add_brackets(mount, van)
mount = add_top_gussets(mount, van)
mount = add_wedge_fillet(mount, van)   # union near the right bracket, don't perturb its fillet
mount = add_plate_corners(mount, van)

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

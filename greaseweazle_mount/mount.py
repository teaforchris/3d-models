"""Greaseweazle V4.1 adapter for a 2.5"->3.5" SSD mounting plate.

Two side pieces. M3 screws come up through the SSD plate's slots (the 2.5"
drive bottom-hole pattern) into each piece. The Greaseweazle lies across the
bay on top of both, held by M2.5x6 self-tapping screws through its own 2.7 mm
holes, so its IDC and USB-C edges face the bay's front and rear. At the -Y end
each piece rises above the plate's flanges to carry a donor front-panel board
(Cooler Master S1013) that is wider than the plate.

Run: uv run python greaseweazle_mount/mount.py            (preview only)
     uv run python greaseweazle_mount/mount.py --export  (+ datetimed STL per side)
Live preview: open the "OCP CAD Viewer" panel first (hot-reloads on save).
"""
import math
import sys
from datetime import datetime
from pathlib import Path

from build123d import *
from ocp_vscode import show

HERE = Path(__file__).parent
OUTPUTS = HERE / "outputs"

# ---- PARAMETERS (everything tunable lives here) ----
# Datum: origin = centre of the SSD hole pattern, Z=0 = SSD plate floor.
# X runs across the bay (61.72 axis), Y front-to-back (76.6 axis).
# The PCB's length runs along X; its IDC edge faces +Y, its USB-C edge -Y.

# SSD plate interface (SFF-8201 bottom holes)
ssd_pitch_x   = 61.72      # mm
ssd_pitch_y   = 76.60      # mm
m3_pilot      = 2.5        # mm  M3 machine screw threads straight into the 2 mm strut
m3_pad_dia    = 7.0        # mm  every strut, arm, ledge and post matches this width.
                           #     Holes go right through, so the +Y screw tips under the
                           #     PCB must stay below board_z
plate_boss_h  = 1.45       # mm  the plate's slot bosses stand this proud of its floor; the
                           #     M3 pads sit on them, on arms raised off the floor

# Side pieces: flat struts on the floor; posts, raised arms and ledges come off them
base_thick    = 2.0        # mm
strut_w       = m3_pad_dia # mm

# Greaseweazle V4.1 (GW_V41_231112 Gerbers)
pcb_len       = 95.0       # mm  along X
pcb_wid       = 50.0       # mm  along Y
pcb_thick     = 1.6        # mm
pcb_corner_r  = 3.0        # mm
gw_pitch_len  = 81.0       # mm  holes 7.0 in from each short edge
gw_usb_inset  = 10.0       # mm  hole centre -> USB-C long edge
gw_idc_inset  = 5.0        # mm  hole centre -> IDC long edge
gw_hole_dia   = 2.7        # mm

# Board mounting
board_z       = 7.0        # mm  plate floor -> PCB underside; clears the plate's side screw holes
gw_idc_row_y  = ssd_pitch_y / 2   # mm  IDC-side hole row, in line with the +Y M3 holes
under_clear   = 4.0        # mm  min gap over the floor struts for through-hole pin tails
standoff_dia  = m3_pad_dia # mm  bare ring round each hole is 5.1; bearing on mask is fine
m25_pilot     = 2.1        # mm  M2.5x6 self-tapper: 1.6 PCB + 4.4 engagement
lead_in       = 0.4        # mm  chamfer on every screw entry: the plastic a self-tapper
                           #     pushes up must not stop the part or PCB seating flat

# Front-panel board (Cooler Master S1013) at the -Y end, ports facing -Y
cm_hole_pitch = 106.3      # mm  outer (M2.5) holes, centre to centre
cm_hole_y     = -ssd_pitch_y / 2   # mm  outer-hole row, in line with the -Y M3 holes
cm_pcb_thick  = 1.6        # mm  assumed

# Front-panel supports: a riser in line with the GW posts, carrying a ledge out over the
# flange to the outer hole. The board's underside is flush there, so it sits on the ledge;
# an M2.5x6 pokes out under the ledge, outside the flange
wall_h        = 11.0       # mm  plate floor -> top of its flanges and the bay's side walls
wall_clear    = 1.0        # mm  min gap, wall tops -> ledge underside
cm_gap        = 6.4        # mm  GW topside -> front-panel PCB underside; a USB-C plug
                           #     fits under it (checked)
ledge_thick   = base_thick # mm

# Plate, for the viewer only
flange_gap    = 99.8       # mm  between the flanges' inner faces (measured)
plate_t       = 1.0        # mm  assumed
plate_ys      = (-67.5, 49.5)  # mm  photo estimate
slot_pair_dy  = 17.9       # mm  each M3 slot has a twin this far toward -Y (photo estimate)

# ---- derived ----
gw_ys  = (gw_idc_row_y - (pcb_wid - gw_usb_inset - gw_idc_inset), gw_idc_row_y)
pcb_cy = gw_idc_row_y + gw_idc_inset - pcb_wid / 2      # PCB outline centre
cm_z    = board_z + pcb_thick + cm_gap                        # front-panel PCB underside
ledge_z = (cm_z - ledge_thick, cm_z)                          # underside, top
riser_cx = gw_pitch_len / 2      # |X|, in line with the GW posts: every strut runs along X or Y

ALIGN_BASE = (Align.CENTER, Align.CENTER, Align.MIN)
ALIGN_TOP = (Align.CENTER, Align.CENTER, Align.MAX)


def strut(a, b, width=strut_w, z=0, thick=base_thick):
    """Round-ended flat strip from point a to point b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    slot = SlotCenterToCenter(math.hypot(dx, dy), width,
                              rotation=math.degrees(math.atan2(dy, dx)))
    return extrude(Pos((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z) * slot, amount=thick)


def build_side(sx):
    """Side piece under the PCB end at sx = -1 (left) or +1 (right)."""
    m3 = [(sx * ssd_pitch_x / 2, y) for y in (-ssd_pitch_y / 2, ssd_pitch_y / 2)]
    so = [(sx * gw_pitch_len / 2, y) for y in gw_ys]
    riser, cm_hole = (sx * riser_cx, cm_hole_y), (sx * cm_hole_pitch / 2, cm_hole_y)

    # Floor struts join only the posts that stand on the plate floor
    part = Part() + [strut(so[0], so[1]), strut(so[0], riser)]
    for x, y in so:
        part += Pos(x, y, 0) * Cylinder(standoff_dia / 2, board_z, align=ALIGN_BASE)
    part += Pos(*riser, 0) * Cylinder(standoff_dia / 2, ledge_z[1], align=ALIGN_BASE)

    # M3 pads sit on the slot bosses, on arms raised out of the post on the same row. The
    # +Y arm runs under the PCB's hole row, clear of its pins.
    for post, pad in ((so[1], m3[1]), (riser, m3[0])):
        part += strut(post, pad, z=plate_boss_h)
        part += Pos(*pad, plate_boss_h) * Cylinder(m3_pad_dia / 2, base_thick, align=ALIGN_BASE)

    # Front-panel ledge out over the flange to the outer hole
    part += strut(riser, cm_hole, width=standoff_dia, z=ledge_z[0], thick=ledge_thick)

    for x, y, top in [(x, y, board_z) for x, y in so] + [(*cm_hole, cm_z)]:   # M2.5, from above
        part -= Pos(x, y, top) * Cylinder(m25_pilot / 2, top, align=ALIGN_TOP)
        part -= Pos(x, y, top) * Cone(m25_pilot / 2, m25_pilot / 2 + lead_in, lead_in,
                                      align=ALIGN_TOP)
    for x, y in m3:                                                         # M3, from below
        part -= Pos(x, y, plate_boss_h) * Cylinder(m3_pilot / 2, base_thick, align=ALIGN_BASE)
        part -= Pos(x, y, plate_boss_h) * Cone(m3_pilot / 2 + lead_in, m3_pilot / 2, lead_in,
                                               align=ALIGN_BASE)
    return part


def build_pcb_ghost():
    """Bare PCB at its mounted height, for checking fit in the viewer. Not exported."""
    pcb = Pos(0, pcb_cy, board_z) * extrude(
        RectangleRounded(pcb_len, pcb_wid, pcb_corner_r), amount=pcb_thick)
    for x in (-gw_pitch_len / 2, gw_pitch_len / 2):
        for y in gw_ys:
            pcb -= Pos(x, y, board_z) * Cylinder(gw_hole_dia / 2, pcb_thick, align=ALIGN_BASE)
    return pcb


def build_cm_ghost():
    """Front-panel PCB at its mounted height. Only the hole pitch is measured; the
    outline (body, end ears, +X tab) is estimated from a photo. Not exported."""
    hx, y0 = cm_hole_pitch / 2, cm_hole_y
    outline = (Pos(0, y0 - 2.75) * Rectangle(2 * (hx - 2.8), 23.1)
               + Pos(0, y0 - 1.7) * Rectangle(2 * (hx + 4.5), 11.8)
               + Pos(38.75, y0 + 12.1) * Rectangle(20.1, 6.6))
    pcb = Pos(0, 0, cm_z) * extrude(outline, amount=cm_pcb_thick)
    for x in (-hx, hx):
        pcb -= Pos(x, y0, cm_z) * Cylinder(1.5, cm_pcb_thick, align=ALIGN_BASE)
    return pcb


def build_plate_ghost():
    """SSD plate floor, side flanges and all eight slot bosses (simplified to rings), for
    checking clearances. Not exported."""
    cy, length = sum(plate_ys) / 2, plate_ys[1] - plate_ys[0]
    plate = Pos(0, cy, 0) * Box(flange_gap + 2 * plate_t, length, plate_t, align=ALIGN_TOP)
    for s in (-1, 1):
        plate += Pos(s * (flange_gap + plate_t) / 2, cy, -plate_t) * Box(
            plate_t, length, wall_h + plate_t, align=ALIGN_BASE)
    ring = (Cylinder(m3_pad_dia / 2, plate_boss_h, align=ALIGN_BASE)
            - Cylinder(1.75, plate_boss_h, align=ALIGN_BASE))
    for x in (-ssd_pitch_x / 2, ssd_pitch_x / 2):
        for y in (-ssd_pitch_y / 2, ssd_pitch_y / 2):
            plate += [Pos(x, y, 0) * ring, Pos(x, y - slot_pair_dy, 0) * ring]
    return plate


assert board_z - base_thick >= under_clear, "floor struts too close to the PCB's pin tails"
assert ledge_z[0] >= wall_h + wall_clear - 1e-9, "ledges too close to the wall tops"
left, right = build_side(-1), build_side(1)
pcb = build_pcb_ghost()
cm = build_cm_ghost()
plate = build_plate_ghost()

if __name__ == "__main__":
    for name, side in (("left", left), ("right", right)):
        print(f"{name}: valid {side.is_valid}, volume {side.volume:.1f} mm^3, "
              f"bbox {side.bounding_box().size}")
    show(left, right, pcb, cm, plate, names=["left", "right", "gw_pcb", "cm_pcb", "plate"],
         colors=["orange", "orange", "purple", "green", "silver"],
         alphas=[1.0, 1.0, 0.5, 0.5, 0.25])
    if "--export" in sys.argv:
        OUTPUTS.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        for name, side in (("left", left), ("right", right)):   # mirror pair; test-print one
            stl = OUTPUTS / f"mount_{name}_{stamp}.stl"
            export_stl(side, str(stl))
            print("exported", stl.relative_to(HERE.parent))

"""Royal Mail Large Letter gauge: a flat frame round a 250 x 25 mm slot.

An item that passes through the slot is within the Large Letter width and
thickness limits. Length (353 mm max) and weight (750 g max) are not checked.
Square-on the frame is wider than the bed, so it prints flat, turned 45°.

Each rail is a truss in the plane of the frame: an inner chord forms the slot
edge, an outer chord the outside edge, and webs zig-zag between them. The frame
may flex out of plane; the truss stops the slot opening under a push.

Run: uv run python royal_mail_gauge/gauge.py            (preview only)
     uv run python royal_mail_gauge/gauge.py --export  (+ datetimed STL)
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
# Datum: origin = slot centre, Z=0 = bed. X runs along the slot's 250 mm width.

# Royal Mail Large Letter limits
slot_w        = 250.0      # mm  max width
slot_h        = 25.0       # mm  max thickness
slot_clear    = 0.0        # mm  added to both slot dimensions. FDM holes print slightly
                           #     undersize, which errs toward rejecting items at the limit

# Frame
thick         = 3.0        # mm  along the item's travel = print height
rail_w        = 20.0       # mm  long sides
end_w         = 8.0        # mm  short ends, solid
lead_in       = 0.4        # mm  chamfer round the slot, bed side only: takes up elephant's foot

# Rail truss
chord_in      = 7.0        # mm  slot edge
chord_out     = 7.0        # mm  outside edge
web           = 3.0        # mm
web_pitch     = 22.0       # mm  target node spacing along each chord; the count is rounded
                           #     to even so a node sits at mid-span
min_cell      = 4.0        # mm^2  smaller openings are left solid

# Printer: Anycubic Kobra 2 Neo
bed           = 220.0      # mm  square printable area (AnycubicSlicerNext profile)
bed_margin    = 3.0        # mm  min gap, part -> bed edge. No room for a skirt or brim

# ---- derived ----
sw, sh = slot_w + slot_clear, slot_h + slot_clear
outer_l, outer_w = sw + 2 * end_w, sh + 2 * rail_w
# At 45° the corner chamfers lie parallel to the bed edges and set the footprint
corner = max(0.0, (outer_l + outer_w - math.sqrt(2) * (bed - 2 * bed_margin)) / 2)
corner_wall = (end_w + rail_w - corner) / math.sqrt(2)   # chamfer face -> slot corner
n_panels = 2 * max(1, round(sw / 2 / web_pitch))
pitch = sw / n_panels


def outer_y(x):
    """Outer chord centreline, +Y side; follows the corner chamfer near the ends."""
    return min(sh / 2 + rail_w - chord_out / 2,
               (outer_l + outer_w) / 2 - corner - abs(x) - chord_out / 2 * math.sqrt(2))


# Web nodes, +Y side: on the inner chord at every pitch, on the outer chord between them
inner_nodes = [(-sw / 2 + k * pitch, sh / 2 + chord_in / 2) for k in range(n_panels + 1)]
outer_nodes = [(x, outer_y(x)) for x in (-sw / 2 + (k + 0.5) * pitch for k in range(n_panels))]


def strut(a, b, width):
    """Round-ended 2D strip from point a to point b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    return Pos((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) * SlotCenterToCenter(
        math.hypot(dx, dy), width, rotation=math.degrees(math.atan2(dy, dx)))


def build_outline():
    outline = Rectangle(outer_l, outer_w)
    return chamfer(outline.vertices(), corner) if corner else outline


def build_face():
    """The frame's plan: outline, slot and truss openings."""
    outline = build_outline()
    inset = offset(outline, -chord_out)
    zigzag = [p for pair in zip(inner_nodes, outer_nodes) for p in pair] + [inner_nodes[-1]]

    face = outline - Rectangle(sw, sh)
    for sy in (1, -1):
        cells = inset & Pos(0, sy * (sh + rail_w + chord_in) / 2) * Rectangle(sw, rail_w - chord_in)
        for a, b in zip(zigzag, zigzag[1:]):
            cells -= strut((a[0], sy * a[1]), (b[0], sy * b[1]), web)
        for cell in cells.faces():
            if cell.area >= min_cell:
                face -= cell
    return face


def build_gauge():
    part = extrude(build_face(), amount=thick)
    slot_edges = part.edges().filter_by(
        lambda e: e.bounding_box().max.Z < 1e-6
        and abs(e.center().X) <= sw / 2 + 1e-6 and abs(e.center().Y) <= sh / 2 + 1e-6)
    return chamfer(slot_edges, lead_in)


def build_bed_ghost():
    """Printable area, centred under the part. Not exported."""
    return Box(bed, bed, 1.0, align=(Align.CENTER, Align.CENTER, Align.MAX))


assert corner_wall >= end_w - 1e-9, "corner chamfers cut too close to the slot"
gauge = Rot(0, 0, 45) * build_gauge()      # as it sits on the bed
bed_ghost = build_bed_ghost()
footprint = gauge.bounding_box().size
assert max(footprint.X, footprint.Y) <= bed - 2 * bed_margin + 1e-6, "gauge overhangs the bed"

if __name__ == "__main__":
    print(f"gauge: valid {gauge.is_valid}, volume {gauge.volume:.1f} mm^3, "
          f"footprint {footprint.X:.1f} x {footprint.Y:.1f} on a {bed:.0f} bed, "
          f"{n_panels} panels at {pitch:.1f}")
    show(gauge, bed_ghost, names=["gauge", "bed"], colors=["orange", "silver"],
         alphas=[1.0, 0.25])
    if "--export" in sys.argv:
        OUTPUTS.mkdir(exist_ok=True)
        stl = OUTPUTS / f"large_letter_{datetime.now():%Y%m%d-%H%M%S}.stl"
        export_stl(gauge, str(stl))
        print("exported", stl.relative_to(HERE.parent))

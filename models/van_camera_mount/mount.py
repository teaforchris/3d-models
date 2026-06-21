"""Van reversing-camera mount — model 1.

PHASE 2: offset the validated van-face curve to add wall thickness, then
extrude across the camera-body width.

Run: uv run python models/van_camera_mount/mount.py
Live preview: open the "OCP CAD Viewer" panel in VS Code first; the script
calls show() at the end and hot-reloads on save.
"""
from pathlib import Path

from build123d import *
from ocp_vscode import show

SVG = Path(__file__).parent / "door_profile.svg"

# ---- PARAMETERS (everything tunable lives here) ----
wall          = 3.0        # mm  wall thickness, added to the NON-van side
extrude_width = 3.0        # mm  mount width (Z) — door assumed flat across this span
                           #     (3 mm = thin test slice to print-check the hook fit)
offset_side   = Side.RIGHT  # 3 mm on the OUTSIDE of the curl, keeps the hook slot open

# The validated van-face curve (open Wire, hook at top). Never hand-edit.
van = import_svg(SVG)[0]

# Offset the open van curve into a closed band (wall thick) on the non-van
# side. Side.LEFT keeps the wall OUTSIDE the rolled-lip curl; Side.RIGHT
# self-intersects there. The original van curve survives as the contact edge.
band = offset(van, amount=wall, side=offset_side, closed=True)
section = make_face(band)
mount_part = extrude(section, amount=extrude_width)
mount = mount_part  # alias for clarity downstream

if __name__ == "__main__":
    bb = mount.bounding_box()
    print("solid volume (mm^3):", round(mount.volume, 1))
    print("bbox size (mm):", bb.size)
    show(mount)

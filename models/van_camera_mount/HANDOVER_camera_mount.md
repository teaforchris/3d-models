# Handover: Van reversing-camera mount (build123d / code-CAD)

You are picking up a CAD project mid-stream. This document is the full context — a previous session did the analysis and planning; your job is to continue the build in Python with **build123d**, give me a live 3D preview to confirm geometry, then build the part out to a printable STL. I'm an experienced developer working in Claude Code, so be direct and technical; assume I can run scripts and read code.

---

## 1. Project summary

I'm making a **custom 3D-printed mount for a reversing camera on the rear door of a van** — the door that houses the brake light and number-plate lights. The wiring is already run inside the door.

The mount works like this:
- It **hooks over the top rolled-steel lip** of the door (the door's top edge is a rolled-over return).
- From the hook it **runs down the door following the exact metal profile** — over the rolled top, around the edge, and flat down the back face of the door (the face you see looking at the closed door).
- It's held in place by **embedded neodymium magnets** in the back face: the install action is "hook over the top, then let the magnets snap/pull it flat." The back contact face must be one continuous surface against the door's back/edge/top.
- Two **arms protrude from the mount** matching the camera's existing mount-hole pattern, secured with **M2 nut + bolt** through the arms into the camera.

The cross-section (the profile described above) is **constant**, so the 3D part is fundamentally: take the 2D profile → add wall thickness → extrude across the camera-body width → add the arms and magnet pockets. It is **prismatic**, not freeform — which is exactly why code-CAD is the right tool.

## 2. Status — what's done

- **The hard part is done and physically validated.** I modelled the van's door-edge profile, 3D-printed a prototype of just that profile, and offered it up to the real van door. It is a **precise, snug fit**. So the door-face curve is geometrically correct against real metal — it must be preserved exactly and never hand-edited.
- That validated curve has been **exported to SVG as a single open spline** (the disposable "closing edge" that only existed to make the prototype printable has been removed). The SVG is embedded below and also provided as `door_profile.svg`.
- **Approach chosen:** build123d (Pythonic parametric CAD on the OpenCASCADE kernel — the same kernel FreeCAD uses) with **ocp-vscode** for a live, hot-reloading 3D preview, driven from Claude Code. This was chosen over driving FreeCAD via an MCP server because the part is prismatic/parametric and code is cleaner here, and it matches my existing Claude Code workflow.

## 3. The validated van-face curve

This is the exact, fit-validated door-metal profile. **Use this curve as-is; never regenerate or hand-edit it** — its whole value is that it matches real metal.

`door_profile.svg`:

```xml
<?xml version="1.0"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="34.96927050083736mm" height="120.23053139047202mm" viewBox="0 0 34.96927050083736 120.23053139047202" xmlns="http://www.w3.org/2000/svg" version="1.1">
<g id="Part__Part2DObjectPython" transform="translate(14.209792,77.272094) scale(1,-1)">
<path id="Part__Part2DObjectPython_w0000"  d="M 18.202311 71.2612 L 18.796574 72.697876 L 18.924004 72.651924 C 20.558062 75.760635 19.666314455797032 76.66388406681088 18.758166960148372 76.88833312223998 C 17.850019464499713 77.11278217766909 16.92547201740536 76.65843122171641 15.663 72.7119 Q -0.3514820000000001 34.9667 -12.945331999999999 -2.5453480000000006 Q -16.095842 -12.636397 -8.55353 -18.434584 Q 5.453518 -30.300375 20.416643 -42.615601 " stroke="#f1f3f5" stroke-width="0.7 px" style="stroke-width:0.7;stroke-miterlimit:4;stroke-dasharray:none;stroke-linecap:square;fill:none;fill-opacity:1;fill-rule: evenodd"/>
<title>b'Part__Part2DObjectPython'</title>
</g>
</svg>
```

**Known facts about this curve (verified):**
- It is a **single open path** (no `Z`, no second subpath) = just the door-metal curve, no closing edge.
- **Bounding box ≈ 34.3 × 119.6 mm**; **developed (along-curve) length ≈ 148 mm**. Units are millimetres (FreeCAD exports 1 SVG user-unit = 1 mm).
- **Two free ends:** the **hook tip ≈ (18.2, 71.26)** (this end tucks under the rolled lip) and the **bottom of the run ≈ (20.42, −42.62)**.
- The **small curl at the top is the rolled steel lip**; the hook tip sits under it. This curl is the **tightest feature on the profile — inner radius < 3 mm** (important for the offset; see Phase 2).
- **Orientation:** the raw `d=""` coordinates are in FreeCAD sketch space, which is **Y-up**. The group `transform="... scale(1,-1)"` only flips it to SVG's Y-down for display. build123d's `import_svg(flip_y=True)` (the default) flips it back, so **after import the hook should land at the TOP**. Confirm this in the preview — build123d has historically had occasional SVG-orientation quirks.

## 4. Environment / setup

- Python 3.10+ (build123d supports >=3.10, <3.15).
- `pip install build123d ocp_vscode`
- Install the **"OCP CAD Viewer"** VS Code extension, and start its viewer. In scripts: `from ocp_vscode import show, show_all`. Call `show(obj)` (or `show_all()`) at the end of the script; the viewer hot-reloads on save. This is the live 3D preview loop — I edit/you edit the `.py`, the viewer re-renders.
- Verify the exact build123d API calls against the installed version as you go (the offset/`add` incantations below are close but versions differ slightly).

---

## 5. PHASE 1 — Import the curve and preview it (do this first)

Goal: get the validated curve into build123d and **show it to me so I can confirm geometry, orientation, and scale before we build anything on top of it.** Put `door_profile.svg` next to the script.

```python
from build123d import *
from ocp_vscode import show

# The validated van-face curve. flip_y=True (default) puts the hook at the top.
van = import_svg("door_profile.svg")[0]   # open Wire

bb = van.bounding_box()
print("type:", type(van).__name__)
print("bbox size (mm):", bb.size)          # expect ~ (34.3, 119.6, 0)
print("is_closed:", getattr(van, "is_closed", "n/a"))

show(van)
```

**Phase 1 verification checklist (confirm with me):**
- The hook/curl is at the **top**.
- Bounding box ≈ **34.3 × 119.6 mm** (i.e. it imported in millimetres, not mangled scale).
- It's a **single open wire** (not closed, not two pieces).

Once confirmed, optionally "bake" the curve into source for version control with `import_svg_as_buildline_code("door_profile.svg")`, which emits pasteable BuildLine code so the geometry lives in the script rather than as a file dependency. (Keep the SVG either way as the source of truth.)

## 6. PHASE 2 — Thickness (offset) + extrude to full width

The contact face = the van curve. Add wall thickness to the **non-van side only** by offsetting the open curve into a thin band, make a face, then extrude across the camera-body width.

```python
from build123d import *
from ocp_vscode import show

# ---- PARAMETERS (everything tunable lives here) ----
wall          = 3.0   # mm  wall thickness, added to the NON-van side
extrude_width = 40.0  # mm  camera-body width (Z) — PLACEHOLDER, confirm real value
offset_side   = Side.LEFT   # FLIP to Side.RIGHT if the 3mm lands on the wrong side

van = import_svg("door_profile.svg")[0]   # open Wire (hook at top)

with BuildPart() as mount:
    with BuildSketch() as section:
        with BuildLine():
            add(van)                       # the exact van curve, untouched
        offset(amount=wall, side=offset_side)   # 3mm band on one side -> closes it
        make_face()
    extrude(amount=extrude_width)

show(mount)
```

**Two critical things:**

1. **Offset direction at the hook is not optional.** The rolled-lip curl has an inner radius < 3 mm, so the 3 mm offset **must go to the OUTSIDE of the curl** (the side away from where the steel sits inside the curl). Offset the wrong way and the hook self-intersects or collapses the gap the lip needs. Set `offset_side` to whichever keeps the wall *off* the metal; if it errors or looks kinked at the hook, flip it. The original van spline must survive as one edge of the resulting face so the contact surface stays bit-for-bit the measured geometry — verify this.

2. **Open question — width curvature (ask me).** A straight `extrude` assumes the door's top is **flat across the width**. My prototype validated the *profile* fit, not the *width* fit. If the rear door also curves **horizontally** across the back, a straight extrude won't make continuous contact across the full width — we'd `sweep()` the profile along a second rail captured across the width instead. **Confirm with me whether the door is flat across the mount width before committing to a straight extrude.** (If the mount is only as wide as the camera body and the door is near-flat over that span, a straight extrude is a fine approximation and the magnets close any sliver of a gap.)

## 7. PHASE 3 — Arms (M2 holes) + magnet pockets

Two features to add. **You need dimensions from me first — ask for these before building Phase 3:**

- **Camera mount holes:** centre-to-centre spacing of the two M2 holes; their position/height relative to the profile; whether they're through-holes or blind.
- **Arms:** how far they project from the mount; arm thickness; arm width; where on the body they attach.
- **Magnets:** diameter, thickness, count, and placement along the back face.

Implementation notes once dimensions are known:
- **Datum:** pick the **back contact face as the reference** and position arms and magnets relative to it.
- **Arms:** model as extrusions/boxes attached to the body, projecting to put the M2 holes at the camera's hole pattern. M2 clearance through-hole ≈ 2.2–2.4 mm diameter (I'm using M2 nut + bolt, so plan for bolt clearance + nut access/seat).
- **Magnet pockets:** **blind** cylinders subtracted from the back face — sized to the magnet diameter/thickness with a small press-fit/glue allowance. Keep them blind (don't break through) so **the back contact face stays one continuous surface against the door.**
- **Export:** `export_stl(mount.part, "camera_mount.stl")` when done (and `export_step(...)` if I want an editable master).

---

## 8. Design principles to honour throughout

- **Fully parametric:** every dimension (`wall`, `extrude_width`, `magnet_dia`, `magnet_depth`, `camera_hole_spacing`, arm geometry, …) is a named variable at the top of the script. Re-tuning anything = one-line change + re-render.
- **The van contact face stays slaved to the imported curve.** Never hand-edit it. If the door points are ever nudged, the offset face and everything downstream should follow automatically.
- **Back contact face = datum**, and keep it continuous (blind magnet pockets, no through-features on it).
- **Preview-driven:** `show()` after each phase in ocp-vscode and confirm with me before moving on.

## 9. Immediate open questions to resolve with me

1. After Phase 1: does the imported curve match — hook at top, ~34 × 120 mm, single open wire?
2. Phase 2: is the door **flat across the mount width** (→ straight extrude) or does it **curve horizontally** (→ sweep along a second rail)?
3. Phase 3 dimensions: M2 hole centre-to-centre spacing, arm projection/thickness/width and attachment point, magnet diameter/thickness/count/placement.

Start with Phase 1, show me the preview, and we'll go from there.

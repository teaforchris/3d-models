# Van reversing-camera mount — project context

3D-printed mount for a reversing camera on a van's rear door (the door with the
brake light / number-plate lights; wiring already run inside). Model 1 of n in
this build123d repo.

## What it is
- **Hooks over the top rolled-steel lip** of the door, then runs down following
  the exact metal profile — over the rolled top, around the edge, flat down the
  back face.
- Held by **embedded neodymium magnets** in the back face: install = hook over
  the top, let the magnets pull it flat. Back contact face must stay **one
  continuous surface** against the door (blind magnet pockets, no through-holes).
- **Two arms** project to the camera's mount-hole pattern, **M2 nut + bolt**.
- Cross-section is **constant** → the part is prismatic: 2D profile → offset for
  wall → extrude across width → add arms + magnet pockets.

## Layout
`sources/` — inputs (the validated `door_profile.svg`). `outputs/` — exported,
datetime-stamped STLs (tracked, never overwritten). Scripts + `CLAUDE.md` +
`profile_labelled.png` live at the model-dir root.

## The contact curve — the one inviolable asset
`sources/door_profile.svg` is a single open spline, **fit-validated against the real
metal** (printed and offered up). Units = mm; hook/curl at the top after
`import_svg` (default `flip_y=True`). bbox ≈ 34.3 × 119.6 mm, developed length
≈ 148 mm. The tight curl (rolled lip) has inner radius < 3 mm.

**Never hand-edit the SVG.** Any shape change is expressed as a **parametric
tweak** in `mount.py` so the validated geometry stays the source of truth and
changes stay reproducible.

## Reference points (shared vocabulary)
`label_profile.py` → `profile_labelled.png`. Walking the curve hook→bottom:
A hook tip · B/C rolled-lip nose (0.1 mm apart) · D crown of curl · E curl
throat (lip enters here) · F leftmost bend (rounds the door edge) · G corner
onto the back face · H bottom free end. A–E enclose the hook throat; E→F is the
long sweep; F→G the arc; G→H the back-face leg.

## Current model state (`mount.py`)
- `offset_side = Side.RIGHT` — wall on the OUTSIDE of the curl (LEFT fills the
  throat and destroys the hook). Contact face stays the validated curve to 0.0 mm.
- `extrude_width` — **3 mm = thin print-test slice**, set to the real mount width
  for the full part.
- Print-test seat tweaks (override validated curve to close rests-gaps on the
  van; both small, feel-tuned, refine by reprint):
  - `ef_extend` — lengthen E→F sweep along its tangent, carry F-G-H rigidly →
    seats F.
  - `fg_extend` — continue F-G arc along its curvature past G; G-H leg follows
    the tangent (no kink) → +ve swings H toward the door (~0.35 mm arc ≈ ~1 mm H).
- Export: `mount.py --export` writes `outputs/mount_w<width>_<datestamp>.stl`.

## Open / TODO
- **Width assumption:** door treated as **flat across the mount width** →
  straight `extrude`. Confirmed negligible curve; revisit with a `sweep` along a
  second rail if a real horizontal curve shows up.
- **Phase 3 (needs measurements):** M2 hole centre-to-centre spacing & height;
  arm projection/thickness/width/attachment; magnet dia/thickness/count/placement.
  Datum = the back contact face. Magnet pockets blind. M2 clearance ≈ 2.2–2.4 mm.
- Export: `export_stl(mount, ...)`, `export_step(...)` for an editable master.

## Workflow
- `uv run python van_camera_mount/mount.py` — builds + `show()`s the part
  (`--export` also writes a datetimed STL to `outputs/`).
- Live preview: open the **OCP CAD Viewer** VS Code panel first (writes
  `~/.ocpvscode`); it hot-reloads on save. If `show()` errors on the port, pass
  `OCP_PORT=3939` (or whatever the panel is listening on).
- Design principle: every dimension is a named parameter at the top of the
  script; preview after each change and confirm before building on top.

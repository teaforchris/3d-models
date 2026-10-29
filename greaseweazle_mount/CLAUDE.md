# Greaseweazle mount — project context

Adapter that mounts a Greaseweazle V4.1 board on a 2.5"->3.5" SSD mounting
plate (Kingston SSDNow style), going into a spare 3.5" bay in a rack server.

## What it is
- **Two side pieces, not a frame**, to keep plastic to a minimum. Every strut,
  arm, ledge and post is 7 mm wide, matching the M3 pads; the struts and arms
  are 2 mm thick.
- **M3 screws come up from under the SSD plate** through its slots, exactly
  where an SSD's bottom holes would be, and thread into the 2 mm pads. No
  thicker bosses, by choice: the only load is cable torque.
- The plate's slot bosses stand **1.45 mm proud** of its floor (found on the
  first test print). The floor struts join only the posts that stand on the
  floor. Each M3 pad sits on its slot boss at the end of an arm raised 1.45 mm,
  coming out of the post on the same row: the +Y arm from the Greaseweazle
  standoff, the -Y arm from the front-panel riser.
- The PCB lies **across the bay** (90° to an SSD), between the plate's side
  flanges, so the IDC ribbon and USB-C have the bay's front and rear to exit.
- PCB underside sits **7 mm above the plate floor**, to clear the plate's
  side-flange screw holes.
- **M2.5x6 self-tapping screws** go through the board's own holes into the
  standoffs. Removable by design — no pins, no heat-staking.
- **Front-panel board:** a donor Cooler Master S1013 (2x USB-A, audio) at the
  -Y end, ports facing -Y, wider than the plate. Each side piece carries a
  riser in line with its Greaseweazle standoffs, so every strut, arm and ledge
  runs along X or Y. A ledge on top reaches out over the flange to the outer
  hole (M2.5 self-tapper into the 2 mm ledge). The board sits flush on the
  ledge: its underside is a flush finish there (checked). No brace: the loads
  are light. The board's underside sits 6.4 mm above the Greaseweazle's topside
  (`cm_gap`, a USB-C plug fits under it), 15 mm above the floor, so the ledges
  clear the 11 mm flange/bay walls (measured) by 2 mm. The M2.5x6 tips poke
  2.4 mm out under the ledges, to 10.6 mm, about 1 mm outside the flange.
- Load is only cable torque during service; the server never moves once racked.
  Cables are connected with the board in hand, then the board is screwed down,
  so no support rail under the IDC header.

## Assembly
The plate's slots run front-to-back, so each piece can slide along them. On the
bench, screw the PCB onto both pieces (it sets their alignment), tighten the M3s
from under the plate, then remove the PCB. In the bay: connect the cables, then
screw the PCB down.

## Dimension sources
- Board: official V4.1 Gerbers (`GW_V41_231112.zip`, keirf/greaseweazle wiki →
  Design Files). PCB 95.0 x 50.0, R3. Holes Ø2.70 NPTH, 81.0 x 35.0 pitch,
  7.0 from short edges, 10.0 from USB-C edge, 5.0 from IDC edge. Ø5.1 bare ring.
- SSD pattern: SFF-8201 Rev 3.4 — 61.72 x 76.60, M3, max screw penetration 3 mm.

## Open / TODO
- `gw_idc_row_y` puts the PCB's IDC-side holes in line with the +Y M3 holes,
  freeing the -Y end of the plate. The two side pieces are a mirrored pair.
- `cm_hole_y` puts the front-panel board's outer holes in line with the -Y M3
  holes (same idea as the Greaseweazle).
- Prints flat on the floor struts. The raised M3 arms (1.45 mm up) and the two
  ledges (~13 mm overhang, 13 mm up) need support.
- The posts and floor struts run 5.9 mm inside the flanges (99.8 mm apart
  between inner faces, measured), past the flanges' threaded bosses. The bay
  screws there must not reach in further.
- Photo estimates, not measurements: the front-panel ghost's outline, the
  plate ghost's length, and the flanges' threaded bosses (Y ≈ 44.8, -0.3,
  -18.4, -59.7). The bay screws through those bosses point inward, so keep
  risers away from them if the hole rows ever move.
- `under_clear` = 4 mm is an assumed pin-tail allowance, not measured.
- Screw pilots (`m3_pilot`, `m25_pilot`) untested — confirm on the first print.

## Workflow
Same as `van_camera_mount`: `uv run python greaseweazle_mount/mount.py`
(`--export` writes one datetimed STL per side to `outputs/`; the sides are
mirror images, so a test print needs only one). The viewer also shows
translucent ghosts of both PCBs and the plate; they are not exported.

# Royal Mail gauge — project context

Push-through size gauge for Royal Mail **Large Letter**: a flat frame round a
250 x 25 mm slot (max width x max thickness). It does not check length (353 mm
max) or weight (750 g max).

## Bed fit
- Printer: Anycubic Kobra 2 Neo, 220 x 220 bed (AnycubicSlicerNext profile).
- Square-on the frame is 266 mm long, so it prints flat, **turned 45°**. The
  STL is exported already turned; the slicer centres it.
- The corner chamfers are sized from `bed` and `bed_margin`: at 45° they lie
  parallel to the bed edges and set the footprint (214 x 214 at 3 mm margin).
  An assert stops the build if the part overhangs the bed.
- No room for a skirt or brim: turn both off in the slicer.

## Stiffness
- 3 mm thick, 20 mm rails. The slot opening under a push depends on rail width
  cubed but on thickness only linearly. Out-of-plane flex is fine.
- Each rail is a truss: 7 mm chords, 3 mm webs. Plane-stress FEA puts it at 92%
  of a solid 20 mm rail's stiffness. Narrower chords or webs drop below 90%.
- `min_cell = 1e9` leaves every opening solid: 1.3 g more, 18 min faster.

## Accuracy
- Slot is nominal (`slot_clear` = 0). FDM holes print slightly undersize, so
  the gauge errs toward rejecting items at the limit.
- 0.4 mm lead-in round the slot, bed side only, to take up elephant's foot.
  The gauging section is the straight part above it.

## Open / TODO
- First print (`large_letter_20261109-192850.stl`) came out well. `slot_clear`
  is still untuned: measure the slot if items at the limit get rejected.
- A Letter gauge (240 x 165 x 5) would fit the bed square-on.

## Workflow
Same as the other models: `uv run python royal_mail_gauge/gauge.py`
(`--export` writes a datetimed STL to `outputs/`). The viewer shows a
translucent bed ghost; it is not exported.

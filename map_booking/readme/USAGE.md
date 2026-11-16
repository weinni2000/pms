## Check the availability of a map

1. Open a map and go to its **Availability** tab.
2. Pick the stay period. Every zone is colored from the bookings overlapping
   those nights: the check-out day itself is not a booked night.
3. Toggle **Refresh** to recompute the colors, e.g. after a booking was made in
   another window.

## Availability rules

- A booking blocks its resources from its start until its end; canceled
  bookings are ignored.
- A zone holding several resources stays free while at least one of them is
  free, and only turns occupied when all of them are booked.
- A zone without resources, or a database without a bridge module, carries no
  availability information and is drawn in the neutral color.
- The **Free** and **Occupied** states, and any state you add (maintenance,
  closed, ...), are records: rename them, recolor them, or translate them
  without touching the code.

## Reuse the same map data elsewhere

`map.booking.map` and `map.booking.zone` expose the data the map needs as
plain dictionaries, ready for the `map_widget` component:

- `map.booking.zone._get_map_shapes(state, colors)` - one zone shape;
- `map.booking.map.preview_data_calculated` - image, zones and legend;
- `map.booking.map.test_preview_data_calculated` - the same, colored for the
  checked stay period.

Override `_get_bookable_units()` on `map.booking.zone` to plug in another
booking engine: append `(unit, is_busy)` pairs to the result of the parent
method, so several engines can coexist on the same map.

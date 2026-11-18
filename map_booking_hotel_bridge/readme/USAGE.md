## Availability rules

- A confirmed (or done) reservation blocks its rooms from check-in until
  check-out; draft and canceled reservations are ignored.
- A folio blocks its rooms unless it is canceled.
- A zone holding several rooms stays free while at least one of them is free,
  and only turns occupied when all of them are booked.
- The check-out day itself is not a booked night: a stay starting on the day a
  reservation ends is still free.

## Demo data

The "Holiday Home" demo map holds two flats and a dormitory whose six beds are
rooms of the "Dormitory Bed" type. Flat 1 and three of the beds are booked
today, so Flat 1 shows occupied while Flat 2 and the dormitory stay free.

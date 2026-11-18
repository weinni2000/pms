## Availability rules

- A booking blocks its resources from its start until its end; canceled
  bookings are ignored.
- A zone holding several resources stays free while at least one of them is
  free, and only turns occupied when all of them are booked.
- The check-out day itself is not a booked night: a stay starting on the day a
  booking ends is still free.

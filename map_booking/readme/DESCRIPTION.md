Turns a plan or photo of your site into an interactive map of its bookable
resources.

Each map is an image with clickable zones drawn on it. A zone lists the resources
it contains (``resource.resource``) and colors itself from the real bookings of
those resources, so a receptionist or a visitor sees at a glance which pitches,
rooms or units are **free** and which are **occupied** for the dates they are
checking.

What books a resource comes from a separate bridge module:
``map_booking_resource_booking_bridge`` colors the zones from Resource Booking
reservations, ``map_booking_pms_bridge`` colors them from PMS reservations.
Without one of them the zones carry no availability information and are drawn in
the neutral color.

The map widget itself (rendering, zooming labels, legend, polygon editor) is
provided by the ``map_widget`` module; this module adds the records, the
availability logic and the backend screens.

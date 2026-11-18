Colors the zones of a ``map_booking`` map from the bookings of the resources
they hold, and files the map screens under the Resource Bookings application.

Each zone lists ``resource.resource`` records. Every ``resource.booking`` that is
not canceled blocks its resources for its whole start/stop range, and a zone is
free as soon as one of its resources is free.

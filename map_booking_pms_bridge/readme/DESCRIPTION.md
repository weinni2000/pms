Colors the zones of a ``map_booking`` map from the PMS reservations of the
properties they hold, and files the map screens under the Properties
application.

Each zone lists ``pms.property`` records, picked one by one or through their
``pms.tag`` tags. Every ``pms.reservation`` that is
booked blocks its property for its whole start/stop range, and a zone is free as
soon as one of its properties is free.

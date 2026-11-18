Colors the zones of a ``map_booking`` map from the reservations and folios of
the hotel rooms they hold (OCA ``vertical-hotel``), and files the map screens
under the Hotel Management application.

Each zone lists ``hotel.room`` records, picked one by one or through their
``hotel.room.type``. Every confirmed ``hotel.reservation`` and every
``hotel.folio`` that is not canceled blocks its rooms for its whole
check-in/check-out range, and a zone is free as soon as one of its rooms is
free.

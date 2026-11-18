# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from .common import HotelMapBookingCommon


@tagged("post_install", "-at_install")
class TestMapBookingZoneHotel(HotelMapBookingCommon):
    def test_zone_is_free_without_reservations(self):
        zone_id = self._create_room_zone(self.room_1_id)
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_confirmed_reservation_occupies_the_zone(self):
        zone_id = self._create_room_zone(self.room_1_id)
        self._create_reservation(self.room_1_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )

    def test_draft_reservation_leaves_the_zone_free(self):
        zone_id = self._create_room_zone(self.room_1_id)
        self._create_reservation(
            self.room_1_id, self._dt(2), self._dt(4), confirm=False
        )
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_cancelled_reservation_leaves_the_zone_free(self):
        zone_id = self._create_room_zone(self.room_1_id)
        reservation_id = self._create_reservation(
            self.room_1_id, self._dt(2), self._dt(4)
        )
        reservation_id.cancel_reservation()
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_folio_occupies_the_zone(self):
        zone_id = self._create_room_zone(self.room_1_id)
        folio_id = self._create_folio_stay(self.room_1_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )
        # A canceled folio no longer holds the room.
        folio_id.state = "cancel"
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_reservation_of_another_room_leaves_the_zone_free(self):
        zone_id = self._create_room_zone(self.room_1_id)
        self._create_reservation(self.room_2_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_zone_with_one_free_room_stays_free(self):
        zone_id = self._create_room_zone(self.room_1_id | self.room_2_id)
        self._create_reservation(self.room_1_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )
        # The zone is only occupied once every one of its rooms is taken.
        self._create_folio_stay(self.room_2_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )

    def test_checkout_day_is_not_a_booked_night(self):
        zone_id = self._create_room_zone(self.room_1_id)
        self._create_reservation(self.room_1_id, self._dt(2), self._dt(4))
        # A stay starting on the former guest's check-out day is still free.
        self.assertEqual(
            zone_id._get_availability_state(self._dt(4), self._dt(6)), "free"
        )
        # Same for a stay ending the day the reservation starts.
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(2)), "free"
        )

    def test_single_instant_check(self):
        zone_id = self._create_room_zone(self.room_1_id)
        self._create_reservation(self.room_1_id, self._dt(2), self._dt(4))
        self.assertEqual(zone_id._get_availability_state(self._dt(3, 9)), "occupied")

    def test_map_items_are_the_rooms(self):
        zone_id = self._create_room_zone(self.room_1_id)
        items = zone_id._get_map_shapes("free")[0]["items"]
        self.assertEqual([item["name"] for item in items], ["Room 101"])

    def test_zone_holds_the_rooms_of_its_room_types(self):
        bed_type_id = self.env["hotel.room.type"].create({"name": "Bed"})
        bed_1_id = self._create_room("Bed 1", bed_type_id)
        bed_2_id = self._create_room("Bed 2", bed_type_id)
        zone_id = self._create_room_zone(
            self.env["hotel.room"], room_type_ids=[Command.set(bed_type_id.ids)]
        )
        units = zone_id._get_bookable_units(self._dt(1), self._dt(3))
        self.assertEqual({unit for unit, _busy in units}, {bed_1_id, bed_2_id})
        # Like a picked one, a room of the type keeps the zone free until it is
        # taken too.
        self._create_reservation(bed_1_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )
        self._create_reservation(bed_2_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )

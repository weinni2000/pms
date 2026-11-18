# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.map_booking_hotel_bridge.tests.common import HotelMapBookingCommon


@tagged("post_install", "-at_install")
class TestHotelReservationMap(HotelMapBookingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_room_type_id = cls.env["hotel.room.type"].create(
            {"name": "Map Booking Test Suite"}
        )
        cls.suite_id = cls._create_room("Suite 201", cls.other_room_type_id)
        cls.zone_1_id = cls._create_room_zone(cls.room_1_id, name="Room 101")
        cls.zone_2_id = cls._create_room_zone(cls.room_2_id, name="Room 102")
        cls.zone_suite_id = cls._create_room_zone(cls.suite_id, name="Suite 201")
        cls.map_id = cls._create_map(cls.zone_1_id | cls.zone_2_id | cls.zone_suite_id)

    def _new_reservation(self, **values):
        values = {
            "partner_id": self.guest_id.id,
            "pricelist_id": self.pricelist_id.id,
            "date_order": self._dt(1),
            "checkin": self._dt(1),
            "checkout": self._dt(3),
            "adults": 1,
            "map_booking_map_calculated_id": self.map_id.id,
            **values,
        }
        return self.env["hotel.reservation"].new(values)

    def _pick(self, reservation_id, room_ids):
        reservation_id.map_booking_room_ids_calculated = room_ids
        reservation_id._onchange_map_booking_room_ids_calculated()

    def _shape(self, reservation_id, zone_id):
        return next(
            shape
            for shape in reservation_id.map_booking_data_calculated["shapes"]
            if shape["zone_id"] == zone_id.id
        )

    def test_picked_room_fills_a_line(self):
        reservation_id = self._new_reservation()
        self._pick(reservation_id, self.room_1_id)
        self.assertEqual(reservation_id.reservation_line.categ_id, self.room_type_id)
        self.assertEqual(
            reservation_id.reservation_line.reserve._origin, self.room_1_id
        )

    def test_rooms_of_one_type_share_a_line(self):
        reservation_id = self._new_reservation()
        self._pick(reservation_id, self.room_1_id)
        self._pick(reservation_id, self.room_1_id | self.room_2_id | self.suite_id)
        lines = reservation_id.reservation_line
        self.assertEqual(len(lines), 2)
        self.assertEqual(
            lines.filtered(
                lambda line_id: line_id.categ_id == self.room_type_id
            ).reserve._origin,
            self.room_1_id | self.room_2_id,
        )
        self.assertEqual(
            lines.filtered(
                lambda line_id: line_id.categ_id == self.other_room_type_id
            ).reserve._origin,
            self.suite_id,
        )

    def test_removed_room_leaves_the_line(self):
        reservation_id = self._new_reservation()
        self._pick(reservation_id, self.room_1_id | self.room_2_id | self.suite_id)
        self._pick(reservation_id, self.room_2_id)
        self.assertEqual(
            reservation_id.reservation_line.reserve._origin, self.room_2_id
        )
        self.assertEqual(reservation_id.reservation_line.categ_id, self.room_type_id)

    def test_picked_rooms_follow_the_lines(self):
        reservation_id = self._new_reservation(
            reservation_line=[
                Command.create(
                    {
                        "categ_id": self.room_type_id.id,
                        "reserve": [Command.set(self.room_2_id.ids)],
                    }
                )
            ]
        )
        self.assertEqual(
            reservation_id.map_booking_room_ids_calculated._origin, self.room_2_id
        )

    def test_zones_are_colored_for_the_stay(self):
        # Room 101 is booked by another guest over part of the stay.
        self._create_reservation(self.room_1_id, self._dt(2), self._dt(5))
        reservation_id = self._new_reservation()
        shape_1 = self._shape(reservation_id, self.zone_1_id)
        shape_2 = self._shape(reservation_id, self.zone_2_id)
        self.assertEqual(shape_1["state"], "occupied")
        self.assertEqual(shape_1["colors"]["fill"], self.state_occupied_id.color)
        self.assertEqual(
            shape_1["items"],
            [
                {
                    "id": self.room_1_id.id,
                    "name": self.room_1_id.name,
                    "selectable": False,
                    "url": False,
                }
            ],
        )
        self.assertEqual(shape_2["state"], "free")
        self.assertTrue(shape_2["items"][0]["selectable"])

    def test_stay_after_the_booking_is_free(self):
        # The check-out day of the other booking is not a booked night.
        self._create_reservation(self.room_1_id, self._dt(2), self._dt(5))
        reservation_id = self._new_reservation(
            date_order=self._dt(5), checkin=self._dt(5), checkout=self._dt(7)
        )
        self.assertEqual(self._shape(reservation_id, self.zone_1_id)["state"], "free")

    def test_no_map_no_data(self):
        reservation_id = self._new_reservation(map_booking_map_calculated_id=False)
        self.assertFalse(reservation_id.map_booking_data_calculated)

    def test_default_map_holds_rooms(self):
        reservation_id = self.env["hotel.reservation"].new({})
        self.assertTrue(
            reservation_id.map_booking_map_calculated_id.zone_ids.filtered(
                lambda zone_id: zone_id.room_ids or zone_id.room_type_ids
            )
        )

    def test_zone_caption_shows_room_capacity(self):
        reservation_id = self._new_reservation()
        self.assertEqual(
            self._shape(reservation_id, self.zone_1_id)["caption"], "2 guests"
        )

    def test_selected_rooms_capacity(self):
        reservation_id = self._new_reservation(adults=3)
        self._pick(reservation_id, self.room_1_id | self.room_2_id)
        self.assertEqual(reservation_id.map_booking_room_count_calculated, 2)
        self.assertEqual(reservation_id.map_booking_capacity_calculated, 4)

    def test_map_follows_the_reserved_rooms(self):
        room_id = self._create_room("Room 301")
        other_map_id = self._create_map(
            self._create_room_zone(room_id, name="Room 301"), name="Annex"
        )
        reservation_id = self._create_reservation(room_id, self._dt(1), self._dt(3))
        self.assertEqual(reservation_id.map_booking_map_calculated_id, other_map_id)
        # A map holding one of the rooms is kept, even if another holds more.
        self._pick(reservation_id, room_id | self.room_1_id | self.room_2_id)
        self.assertEqual(reservation_id.map_booking_map_calculated_id, other_map_id)

    def test_map_switches_when_its_rooms_are_gone(self):
        room_id = self._create_room("Room 301")
        other_map_id = self._create_map(
            self._create_room_zone(room_id, name="Room 301"), name="Annex"
        )
        reservation_id = self._new_reservation()
        self._pick(reservation_id, self.room_1_id)
        self.assertEqual(reservation_id.map_booking_map_calculated_id, self.map_id)
        self._pick(reservation_id, room_id)
        self.assertEqual(reservation_id.map_booking_map_calculated_id, other_map_id)

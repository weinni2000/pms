# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHotelReservation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.room_type_id = cls.env["hotel.room.type"].create(
            {"name": "Development Test Room Type"}
        )
        cls.room_1_id = cls._create_room("Room 901")
        cls.room_2_id = cls._create_room("Room 902")

    @classmethod
    def _create_room(cls, name):
        return cls.env["hotel.room"].create(
            {
                "name": name,
                "room_categ_id": cls.room_type_id.id,
                "capacity": 2,
                "isroom": True,
            }
        )

    def test_rooms_of_all_lines_are_listed(self):
        now = fields.Datetime.now()
        reservation_id = self.env["hotel.reservation"].create(
            {
                "partner_id": self.env["res.partner"].create({"name": "Guest"}).id,
                "pricelist_id": self.env["product.pricelist"]
                .create({"name": "Development Test Pricelist"})
                .id,
                "date_order": now,
                "checkin": now + timedelta(days=1),
                "checkout": now + timedelta(days=3),
                "adults": 1,
                "reservation_line": [
                    Command.create(
                        {
                            "categ_id": self.room_type_id.id,
                            "reserve": [Command.set(room_id.ids)],
                        }
                    )
                    for room_id in self.room_1_id | self.room_2_id
                ],
            }
        )
        self.assertEqual(
            reservation_id.room_calculated_ids, self.room_1_id | self.room_2_id
        )
        reservation_id.reservation_line[1].unlink()
        self.assertEqual(reservation_id.room_calculated_ids, self.room_1_id)

# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.map_booking.tests.common import MapBookingCommon


class HotelMapBookingCommon(MapBookingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_id = cls.env["res.partner"].create({"name": "Guest"})
        cls.pricelist_id = cls.env["product.pricelist"].create(
            {"name": "Map Booking Test Pricelist"}
        )
        cls.room_type_id = cls.env["hotel.room.type"].create(
            {"name": "Map Booking Test Room Type"}
        )
        cls.room_1_id = cls._create_room("Room 101")
        cls.room_2_id = cls._create_room("Room 102")

    @classmethod
    def _create_room(cls, name, room_type_id=None):
        return cls.env["hotel.room"].create(
            {
                "name": name,
                "room_categ_id": (room_type_id or cls.room_type_id).id,
                "capacity": 2,
                "isroom": True,
            }
        )

    @classmethod
    def _create_reservation(cls, room_id, start, stop, confirm=True):
        reservation_id = cls.env["hotel.reservation"].create(
            {
                "partner_id": cls.guest_id.id,
                "pricelist_id": cls.pricelist_id.id,
                "date_order": start,
                "checkin": start,
                "checkout": stop,
                "adults": 1,
                "reservation_line": [
                    Command.create(
                        {
                            "categ_id": room_id.room_categ_id.id,
                            "reserve": [Command.set(room_id.ids)],
                        }
                    )
                ],
            }
        )
        if confirm:
            reservation_id.confirmed_reservation()
        return reservation_id

    @classmethod
    def _create_folio_stay(cls, room_id, start, stop):
        folio_id = cls.env["hotel.folio"].create(
            {
                "date_order": start,
                "partner_id": cls.guest_id.id,
                "partner_invoice_id": cls.guest_id.id,
                "partner_shipping_id": cls.guest_id.id,
                "pricelist_id": cls.pricelist_id.id,
            }
        )
        cls.env["folio.room.line"].create(
            {
                "room_id": room_id.id,
                "check_in": start,
                "check_out": stop,
                "folio_id": folio_id.id,
            }
        )
        return folio_id

    @classmethod
    def _create_room_zone(cls, room_id, **values):
        values.setdefault("name", "Zone")
        values.setdefault("points", "10,10 110,10 110,60 10,60")
        values["room_ids"] = [Command.set(room_id.ids)]
        return cls.env["map.booking.zone"].create(values)

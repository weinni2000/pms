# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# The hotel occupancy lines store a stay in check_in/check_out instead of the
# start/stop fields `_overlap_domain` is written for.
HOTEL_STAY_FIELDS = {"start": "check_in", "stop": "check_out"}


class MapBookingZone(models.Model):
    _inherit = "map.booking.zone"

    room_ids = fields.Many2many(
        "hotel.room",
        string="Rooms",
        help="Bookable hotel rooms inside this zone.",
    )
    room_type_ids = fields.Many2many(
        "hotel.room.type",
        string="Room Types",
        help="Every room of one of these types is inside this zone, next to "
        "the rooms picked one by one.",
    )

    def _get_bookable_units(self, start=None, end=None):
        """Mark the zone's rooms busy while a reservation or folio covers the stay."""
        self.ensure_one()
        units = super()._get_bookable_units(start, end)
        rooms = self._get_zone_rooms()
        busy_room_ids = set()
        if start and rooms:
            busy_room_ids = set(self._get_busy_rooms(rooms, start, end).ids)
        return units + [(room_id, room_id.id in busy_room_ids) for room_id in rooms]

    def _get_zone_rooms(self):
        """The zone's rooms: those picked plus those of its room types."""
        self.ensure_one()
        room_ids = self.room_ids
        if self.room_type_ids:
            room_ids |= self.env["hotel.room"].search(
                [("room_categ_id", "in", self.room_type_ids.ids)]
            )
        return room_ids

    @api.model
    def _get_hotel_stay_domain(self, start, end=None):
        """`_overlap_domain` on the check_in/check_out fields of hotel lines."""
        return [
            (HOTEL_STAY_FIELDS[name], operator, value)
            for name, operator, value in self._overlap_domain(start, end)
        ]

    @api.model
    def _get_busy_rooms(self, rooms, start, end=None):
        """Rooms occupied during the stay by a reservation or a folio.

        A confirmed (or already checked-in, ``done``) reservation books its
        rooms; draft and canceled ones do not. A folio books its rooms unless
        it is canceled, the same rule the hotel_reservation room picker uses.
        """
        stay_domain = self._get_hotel_stay_domain(start, end)
        reservation_line_id = self.env["hotel.room.reservation.line"].search(
            [
                ("room_id", "in", rooms.ids),
                ("status", "in", ("confirm", "done")),
                *stay_domain,
            ]
        )
        folio_room_line_id = self.env["folio.room.line"].search(
            [
                ("room_id", "in", rooms.ids),
                ("status", "!=", "cancel"),
                *stay_domain,
            ]
        )
        return reservation_line_id.room_id | folio_room_line_id.room_id

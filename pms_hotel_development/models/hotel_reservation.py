# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    room_calculated_ids = fields.Many2many(
        comodel_name="hotel.room",
        string="Rooms",
        compute="_compute_room_calculated_ids",
    )

    @api.depends("reservation_line.reserve")
    def _compute_room_calculated_ids(self):
        for reservation_id in self:
            reservation_id.room_calculated_ids = reservation_id.mapped(
                "reservation_line.reserve"
            )

# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, models


class MapBookingMap(models.Model):
    _inherit = "map.booking.map"

    def action_generate_zones_from_rooms(self):
        """Create one zone per hotel room not linked to a zone yet."""
        self.ensure_one()
        assigned_room_id = (
            self.env["map.booking.zone"].search([("room_ids", "!=", False)]).room_ids
        )
        unassigned_room_id = self.env["hotel.room"].search(
            [("id", "not in", assigned_room_id.ids)]
        )
        self.env["map.booking.zone"].create(
            [
                {
                    "name": room_id.name,
                    "map_id": self.id,
                    "room_ids": [Command.set(room_id.ids)],
                }
                for room_id in unassigned_room_id
            ]
        )

    @api.depends(
        "zone_ids.room_ids",
        "zone_ids.room_ids.active",
        "zone_ids.room_type_ids",
    )
    def _compute_test_preview_data_calculated(self):
        # Odoo merges the dependencies of an overridden compute method, so the
        # base ones keep triggering; this only adds the rooms and room types of
        # a zone.
        return super()._compute_test_preview_data_calculated()

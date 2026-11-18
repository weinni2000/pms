# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, models


class MapBookingMap(models.Model):
    _inherit = "map.booking.map"

    def action_generate_zones_from_properties(self):
        """Create one zone per property not linked to a zone yet."""
        self.ensure_one()
        assigned_property_id = (
            self.env["map.booking.zone"]
            .search([("property_ids", "!=", False)])
            .property_ids
        )
        unassigned_property_id = self.env["pms.property"].search(
            [("id", "not in", assigned_property_id.ids)]
        )
        self.env["map.booking.zone"].create(
            [
                {
                    "name": property_id.name,
                    "map_id": self.id,
                    "property_ids": [Command.set(property_id.ids)],
                }
                for property_id in unassigned_property_id
            ]
        )

    @api.depends(
        "zone_ids.property_ids",
        "zone_ids.property_ids.active",
        "zone_ids.property_tag_ids",
    )
    def _compute_test_preview_data_calculated(self):
        # Odoo merges the dependencies of an overridden compute method, so the
        # base ones keep triggering; this only adds the properties and tags of
        # a zone.
        return super()._compute_test_preview_data_calculated()

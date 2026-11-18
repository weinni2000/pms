# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MapBookingZone(models.Model):
    _inherit = "map.booking.zone"

    def _get_bookable_units(self, start=None, end=None):
        """Mark the zone's resources busy while a booking covers the stay."""
        self.ensure_one()
        units = super()._get_bookable_units(start, end)
        resources = self.resource_ids
        busy_resource_ids = set()
        if start and resources:
            bookings = self.env["resource.booking"].search(
                [
                    ("state", "!=", "canceled"),
                    ("combination_id.resource_ids", "in", resources.ids),
                    *self._overlap_domain(start, end),
                ]
            )
            busy_resource_ids = set(bookings.combination_id.resource_ids.ids)
        return units + [
            (resource, resource.id in busy_resource_ids) for resource in resources
        ]

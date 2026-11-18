# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    def _get_map_booking_website_map(self):
        """The map shown in the booking dialog of this property.

        The first map (in the maps' order) with a zone holding the property,
        picked one by one or through one of its tags.
        """
        self.ensure_one()
        domain = [("property_ids", "in", self.ids)]
        if self.tag_ids:
            domain = ["|", *domain, ("property_tag_ids", "in", self.tag_ids.ids)]
        zone_ids = self.env["map.booking.zone"].sudo().search(domain)
        return zone_ids.map_id.sorted()[:1]

    def _is_map_booking_website_bookable(self):
        """Whether a visitor of the current website may switch to it."""
        self.ensure_one()
        # Same rule as can_access_from_current_website(), which needs a request.
        website_id = self.env["website"].get_current_website()
        return self.is_published and (
            not self.website_id or self.website_id == website_id
        )

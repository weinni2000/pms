# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MapBookingZone(models.Model):
    _inherit = "map.booking.zone"

    property_ids = fields.Many2many(
        "pms.property",
        string="Properties",
        help="Bookable properties inside this zone.",
    )
    property_tag_ids = fields.Many2many(
        "pms.tag",
        string="Property Tags",
        help="Every property carrying one of these tags is inside this zone, "
        "next to the properties picked one by one.",
    )

    def _get_bookable_units(self, start=None, end=None):
        """Mark the zone's properties busy while a reservation covers the stay."""
        self.ensure_one()
        units = super()._get_bookable_units(start, end)
        properties = self._get_zone_properties()
        busy_property_ids = set()
        if start and properties:
            reservations = self.env["pms.reservation"].search(
                [
                    ("property_id", "in", properties.ids),
                    ("stage_id", "not in", self._get_non_blocking_stage_ids()),
                    *self._overlap_domain(start, end),
                ]
            )
            busy_property_ids = set(reservations.property_id.ids)
        return units + [
            (property_id, property_id.id in busy_property_ids)
            for property_id in properties
        ]

    def _get_zone_properties(self):
        """The zone's properties: those picked plus those carrying its tags."""
        self.ensure_one()
        property_ids = self.property_ids
        if self.property_tag_ids:
            property_ids |= self.env["pms.property"].search(
                [("tag_ids", "in", self.property_tag_ids.ids)]
            )
        return property_ids

    @api.model
    def _get_non_blocking_stage_ids(self):
        """Stages whose reservations do not occupy the property.

        Draft reservations are not booked yet and canceled ones are gone, the
        same exclusion the pms_website_sale availability check makes.
        """
        stages = self.env["pms.stage"]
        for xmlid in ("pms_sale.pms_stage_new", "pms_sale.pms_stage_cancelled"):
            stages |= self.env.ref(xmlid, raise_if_not_found=False)
        return stages.ids

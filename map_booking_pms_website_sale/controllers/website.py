# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import http
from odoo.http import request

from odoo.addons.pms_website_sale.controllers.website import PmsWebsiteSale


class MapBookingPmsWebsiteSale(PmsWebsiteSale):
    def _prepare_property_values(self, pms_property, category, search, **kwargs):
        values = super()._prepare_property_values(
            pms_property, category, search, **kwargs
        )
        values["map_booking_map"] = pms_property.sudo()._get_map_booking_website_map()
        return values

    @staticmethod
    def _parse_map_booking_date(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d") if value else None
        except ValueError:
            return None

    @http.route(
        ["/property/<int:property_id>/map_booking"],
        type="jsonrpc",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def property_map_booking(
        self, property_id, date_start=None, date_end=None, **kwargs
    ):
        """Map of the property, colored for the stay picked in the dialog."""
        property_id = request.env["pms.property"].sudo().browse(property_id)
        if not property_id.exists() or not (
            property_id._is_map_booking_website_bookable()
        ):
            return {}
        map_id = property_id._get_map_booking_website_map()
        if not map_id:
            return {}
        start = self._parse_map_booking_date(date_start)
        end = self._parse_map_booking_date(date_end)
        if not (start and end and start < end):
            start = end = None
        return map_id._get_pms_website_data(start, end)

    @http.route(
        ["/map_booking_pms_website_sale/map/<int:map_id>/image"],
        type="http",
        auth="public",
        website=True,
    )
    def map_booking_image(self, map_id, **kwargs):
        """Picture of a map holding a property the visitor can book."""
        map_id = request.env["map.booking.map"].sudo().browse(map_id)
        property_ids = map_id.exists().zone_ids.mapped(
            lambda zone_id: zone_id._get_zone_properties()
        )
        if not property_ids.filtered(
            lambda property_id: property_id._is_map_booking_website_bookable()
        ):
            raise request.not_found()
        return (
            request.env["ir.binary"]
            ._get_image_stream_from(map_id, "image")
            .get_response()
        )

# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.map_booking.models.map_booking_state import STATE_FREE, STATE_OCCUPIED


class MapBookingMap(models.Model):
    _inherit = "map.booking.map"

    def _get_pms_website_image_url(self):
        """Public URL of the map picture (website visitors cannot read maps)."""
        self.ensure_one()
        url = f"/map_booking_pms_website_sale/map/{self.id}/image"
        if not self.write_date:
            return url
        return f"{url}?unique={self.write_date.isoformat()}"

    def _get_pms_website_data(self, start=None, end=None):
        """Map data for the booking dialog of a property.

        Each zone lists its properties as items: an item is selectable when the
        visitor may book it and it is free during the stay. Without a stay the
        zones carry no availability state.
        """
        self.ensure_one()
        colors_by_code = self.env["map.booking.state"]._get_colors_by_code()
        shapes = []
        for zone_id in self.zone_ids:
            units = [
                (unit, busy)
                for unit, busy in zone_id._get_bookable_units(start, end)
                if unit._name == "pms.property"
            ]
            state = False
            if start and units:
                free = any(not busy for _unit, busy in units)
                state = STATE_FREE if free else STATE_OCCUPIED
            colors = colors_by_code.get(state) if state else None
            for shape in zone_id._get_map_shapes(state, colors):
                shape["items"] = [
                    {
                        "id": unit.id,
                        "name": unit.name,
                        "selectable": not busy
                        and unit._is_map_booking_website_bookable(),
                        "url": False,
                        "website_url": unit.website_url,
                    }
                    for unit, busy in units
                ]
                shapes.append(shape)
        return {
            "image_url": self._get_pms_website_image_url(),
            "shapes": shapes,
            "legend": self._get_availability_legend(),
            "legend_position": self._get_legend_position(),
            "label_scale": self.label_scale or 1,
        }

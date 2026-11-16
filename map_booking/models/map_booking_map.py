# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.image import base64_to_image

from .._const import LEGEND_POSITIONS


class MapBookingMap(models.Model):
    _name = "map.booking.map"
    _description = "Map Booking Map"
    _order = "name, id"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    image = fields.Binary(required=True, attachment=True)
    image_filename = fields.Char()
    show_legend = fields.Boolean(
        default=True,
        help="Display a color legend on the map.",
    )
    legend_position = fields.Selection(
        LEGEND_POSITIONS,
        default="bottom_left",
        required=True,
        help="Where the color legend sits on the map.",
    )
    label_scale = fields.Float(
        default=1.0,
        help="Zoom factor for the zone labels shown on the map preview.",
    )
    zone_ids = fields.One2many("map.booking.zone", "map_id", string="Zones")
    preview_data_calculated = fields.Json(compute="_compute_preview_data_calculated")
    availability_check_start = fields.Date(
        string="Check-in",
        default=fields.Date.context_today,
    )
    availability_check_end = fields.Date(
        string="Check-out",
        default=lambda self: fields.Date.context_today(self) + timedelta(days=1),
    )
    refresh = fields.Boolean(
        help="Toggle to force the tested availability to recompute, e.g. after "
        "a booking was made in another window.",
    )
    test_preview_data_calculated = fields.Json(
        compute="_compute_test_preview_data_calculated"
    )

    def action_generate_zones_from_resources(self):
        """Create one zone per material resource not linked to a zone yet."""
        self.ensure_one()
        assigned_resource_ids = (
            self.env["map.booking.zone"]
            .search([("resource_ids", "!=", False)])
            .resource_ids
        )
        resources = self.env["resource.resource"].search(
            [
                ("id", "not in", assigned_resource_ids.ids),
                ("resource_type", "=", "material"),
            ]
        )
        self.env["map.booking.zone"].create(
            [
                {
                    "name": resource.name,
                    "map_id": self.id,
                    "resource_ids": [Command.set(resource.ids)],
                }
                for resource in resources
            ]
        )

    def _get_legend_position(self):
        """Configured legend position, or 'none' when the legend is hidden."""
        self.ensure_one()
        return self.legend_position if self.show_legend else "none"

    def _get_availability_legend(self):
        """Legend items [{label, color}] for the availability states."""
        self.ensure_one()
        return [
            {"label": colors["label"], "color": colors["fill"]}
            for colors in self.env["map.booking.state"]._get_map_colors().values()
            if colors.get("label")
        ]

    def _get_image_size(self):
        """(width, height) of the map image in pixels, or None if unknown."""
        self.ensure_one()
        if not self.image:
            return None
        try:
            return base64_to_image(self.image).size
        except UserError:
            # Not a picture the server can read: nothing to measure against.
            return None

    def _get_image_url(self):
        self.ensure_one()
        if not isinstance(self.id, int):
            # Unsaved record: nothing has been uploaded to preview yet.
            return False
        # For a saved map (image is required), always serve the stored image
        # from the DB. Don't gate on `self.image`: during an onchange the web
        # client omits the binary, which would otherwise make this flip to a
        # blank preview.
        url = f"/web/image/map.booking.map/{self.id}/image"
        # Cache-buster so a newly uploaded image isn't served stale.
        if not self.write_date:
            return url
        return f"{url}?unique={self.write_date.isoformat()}"

    def _to_utc_naive(self, date):
        """User-local date, as the naive UTC datetime Odoo stores.

        The check dates are entered (and defaulted) in the user's timezone,
        while bookings are stored in UTC: combining the date with midnight
        directly would shift the stay window by the user's UTC offset and count
        bookings of the neighbouring night.
        """
        self.ensure_one()
        if not date:
            return False
        tz = ZoneInfo(self.env.user.tz or "UTC")
        local_midnight = datetime.combine(date, time.min, tzinfo=tz)
        return local_midnight.astimezone(timezone.utc).replace(tzinfo=None)

    @api.depends(
        "image",
        "zone_ids.name",
        "zone_ids.code",
        "zone_ids.symbol",
        "zone_ids.points",
        "show_legend",
        "legend_position",
    )
    def _compute_preview_data_calculated(self):
        for map_id in self:
            # Only this map's own zones — not every zone globally, otherwise
            # zones belonging to another map (or orphan/demo zones with points)
            # would render on top of this map's preview.
            zones = map_id.zone_ids
            shapes = []
            for zone_id in zones:
                shapes += zone_id._get_map_shapes()
            map_id.preview_data_calculated = {
                "map_id": map_id.id if isinstance(map_id.id, int) else False,
                "image_url": map_id._get_image_url(),
                "zones": [
                    {
                        "id": zone_id.id,
                        "name": zone_id.name,
                        "code": zone_id.code,
                        "symbol": zone_id.symbol,
                        "map_id": zone_id.map_id.id,
                    }
                    for zone_id in zones
                ],
                "shapes": shapes,
                "legend": map_id._get_availability_legend(),
                "legend_position": map_id._get_legend_position(),
            }

    @api.depends(
        "image",
        "zone_ids",
        "zone_ids.points",
        "zone_ids.resource_ids",
        "zone_ids.resource_ids.active",
        "availability_check_start",
        "availability_check_end",
        "refresh",
        "show_legend",
        "legend_position",
    )
    def _compute_test_preview_data_calculated(self):
        # One query for every state's colors, shared by all the zones below.
        colors_by_code = self.env["map.booking.state"]._get_colors_by_code()
        for map_id in self:
            # Color every zone on this map from the map's test parameters
            # (checked stay range), reusing the per-zone availability logic.
            # Nights only: a night spans [date 00:00, next date 00:00), so the
            # stay covers [check-in 00:00, check-out 00:00) and the check-out
            # day is not itself a booked night.
            start_dt = map_id._to_utc_naive(map_id.availability_check_start)
            end_dt = map_id._to_utc_naive(map_id.availability_check_end)
            shapes = []
            for zone_id in map_id.zone_ids:
                state = (
                    zone_id._get_availability_state(start_dt, end_dt)
                    if start_dt
                    else False
                )
                shapes += zone_id._get_map_shapes(state, colors_by_code.get(state))
            map_id.test_preview_data_calculated = {
                "map_id": map_id.id if isinstance(map_id.id, int) else False,
                "image_url": map_id._get_image_url(),
                "shapes": shapes,
                "legend": map_id._get_availability_legend(),
                "legend_position": map_id._get_legend_position(),
            }

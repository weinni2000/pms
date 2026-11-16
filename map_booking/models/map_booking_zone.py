# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .._const import SYMBOL_SELECTION
from .map_booking_state import STATE_FREE, STATE_OCCUPIED


class MapBookingZone(models.Model):
    _name = "map.booking.zone"
    _description = "Map Booking Zone"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(help="Short text drawn inside the zone on the map.")
    symbol = fields.Selection(
        SYMBOL_SELECTION,
        help="Icon drawn above the zone code on the map.",
    )
    map_id = fields.Many2one("map.booking.map", ondelete="cascade")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    points = fields.Char(
        help=(
            "Polygon outline of this zone on the map image, as SVG points in "
            'the image\'s own pixel space: "x1,y1 x2,y2 x3,y3 ...".'
        ),
    )
    resource_ids = fields.Many2many(
        "resource.resource",
        string="Resources",
        help="Bookable resources inside this zone.",
    )

    @api.constrains("points", "map_id")
    def _check_points(self):
        for zone_id in self:
            if not zone_id.points:
                continue
            points = zone_id._parse_points(zone_id.points)
            if len(points) < 3:
                raise ValidationError(
                    self.env._(
                        "The outline of zone %(zone)s needs at least three points.",
                        zone=zone_id.display_name,
                    )
                )
            size = zone_id.map_id and zone_id.map_id._get_image_size()
            if not size:
                continue
            width, height = size
            if any(not (0 <= x <= width and 0 <= y <= height) for x, y in points):
                raise ValidationError(
                    self.env._(
                        "The outline of zone %(zone)s must stay inside the map "
                        "image (%(width)s x %(height)s pixels).",
                        zone=zone_id.display_name,
                        width=width,
                        height=height,
                    )
                )

    @api.model
    def _parse_points(self, points):
        """[(x, y), ...] of a points string, raising on a malformed value."""
        message = self.env._(
            "Invalid zone outline %(points)s: expected coordinates as "
            '"x1,y1 x2,y2 ...".',
            points=points,
        )
        result = []
        for pair in points.split():
            parts = pair.split(",")
            if len(parts) != 2:
                raise ValidationError(message)
            try:
                result.append((float(parts[0]), float(parts[1])))
            except ValueError as error:
                raise ValidationError(message) from error
        return result

    def _get_availability_state(self, start=None, end=None):
        """free/occupied state code of this zone for the given stay.

        A zone is free as soon as one of its bookable units is free, and
        occupied only when all of them are booked. Zones without bookable
        units, or without an installed booking engine, carry no availability
        information.
        """
        self.ensure_one()
        units = self._get_bookable_units(start or fields.Datetime.now(), end)
        if not units:
            return False
        if any(not busy for _unit, busy in units):
            return STATE_FREE
        return STATE_OCCUPIED

    def _get_bookable_units(self, start=None, end=None):
        """(unit, is_busy) pairs of the bookable units of this zone.

        A unit is a record of any model a booking engine can book, and
        `is_busy` tells whether it is booked during the stay. This module knows
        how to draw and color zones, but not what books their units, so the
        default returns nothing and a zone carries no availability information.

        Bridge modules override this, appending their own units to
        `super()._get_bookable_units()` so several booking engines can coexist.
        """
        self.ensure_one()
        return []

    @staticmethod
    def _overlap_domain(start, end=None):
        """Domain selecting records with start/stop fields that cover the stay.

        Two intervals overlap iff each starts before the other ends. Without an
        end, the stay is the single instant `start`. The strict comparison
        keeps a check-out day out of the booked nights.
        """
        if end and end > start:
            return [("start", "<", end), ("stop", ">", start)]
        return [("start", "<=", start), ("stop", ">", start)]

    def _get_map_shapes(self, state=False, colors=None):
        """Zone data for the `map_widget` component."""
        self.ensure_one()
        if not self.points:
            return []
        if colors is None:
            colors = self.env["map.booking.state"]._get_colors_for_code(state)
        return [
            {
                "id": f"zone-{self.id}",
                "zone_id": self.id,
                "name": self.name,
                "code": self.code,
                "symbol": self.symbol,
                "points": self.points,
                "items": self._get_map_items(state),
                "state": state,
                # Colors resolved from the map.booking.state model so the map
                # renders straight from that single source of truth.
                "colors": colors,
            }
        ]

    def _get_map_items(self, state=False):
        self.ensure_one()
        return [
            {
                "id": unit.id,
                "name": unit.name,
                "selectable": state == STATE_FREE,
                "url": False,
            }
            for unit, _busy in self._get_bookable_units()
        ]

    def action_open_form(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "map.booking.zone",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

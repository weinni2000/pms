# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# Canonical availability-state codes. They are the single source of truth for
# the identifiers used by the availability logic and are mirrored by the
# `code` of the records shipped in data. Import these constants instead of
# hard-coding the strings.
STATE_FREE = "free"
STATE_OCCUPIED = "occupied"


class MapBookingState(models.Model):
    _name = "map.booking.state"
    _description = "Map Booking Availability State"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help="Technical identifier used by the availability logic "
        "(e.g. free, occupied).",
    )
    color = fields.Char(
        string="Fill Color",
        required=True,
        help="Main fill color of a zone in this state, as a CSS color (e.g. #198754).",
    )
    stroke_color = fields.Char(
        string="Border Color",
        help="Outline color of a zone in this state. Defaults to the fill color.",
    )
    hover_color = fields.Char(
        string="Hover Fill Color",
        help="Fill color when the zone is hovered or selected. Defaults to the "
        "fill color.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _map_booking_state_code_uniq = models.Constraint(
        "unique(code)",
        "Each map availability state code must be unique.",
    )

    @api.model
    def _get_map_colors(self):
        """code -> {fill, stroke, hover, label} for every active state.

        Single source of truth for how availability states are labelled and
        colored on the map, both in the backend preview and on public pages.
        """
        result = {}
        # `code` is required, so this only skips the empty-domain warning.
        for state in self.sudo().search([("code", "!=", False)]):
            result[state.code] = {
                "fill": state.color or "",
                "stroke": state.stroke_color or state.color or "",
                "hover": state.hover_color or state.color or "",
                "label": state.name or "",
            }
        return result

    @api.model
    def _get_colors_by_code(self):
        """code -> {fill, stroke, hover} for every active state, in one query.

        Same data as `_get_colors_for_code`, for callers that color several
        zones in a row: fetching the map once avoids one search per zone.
        """
        return {
            code: {key: value for key, value in colors.items() if key != "label"}
            for code, colors in self._get_map_colors().items()
        }

    @api.model
    def _get_colors_for_code(self, code):
        """{fill, stroke, hover} for a single state code, or None."""
        if not code:
            return None
        state_id = self.sudo().search([("code", "=", code)], limit=1)
        if not state_id:
            return None
        return {
            "fill": state_id.color or "",
            "stroke": state_id.stroke_color or state_id.color or "",
            "hover": state_id.hover_color or state_id.color or "",
        }

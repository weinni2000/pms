# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import MapBookingCommon


@tagged("post_install", "-at_install")
class TestMapBookingState(MapBookingCommon):
    def test_map_colors(self):
        colors = self.env["map.booking.state"]._get_map_colors()
        self.assertEqual(colors["free"]["label"], "Free")
        self.assertEqual(colors["free"]["fill"], "#198754")
        self.assertEqual(colors["free"]["stroke"], "#146c43")
        self.assertEqual(colors["free"]["hover"], "#22a06b")
        self.assertEqual(colors["occupied"]["label"], "Occupied")

    def test_colors_by_code_drops_the_label(self):
        colors = self.env["map.booking.state"]._get_colors_by_code()
        self.assertEqual(sorted(colors["free"]), ["fill", "hover", "stroke"])

    def test_colors_for_code(self):
        State = self.env["map.booking.state"]
        self.assertEqual(
            State._get_colors_for_code("free"),
            {"fill": "#198754", "stroke": "#146c43", "hover": "#22a06b"},
        )
        self.assertIsNone(State._get_colors_for_code("unknown"))
        self.assertIsNone(State._get_colors_for_code(False))

    def test_border_colors_fall_back_on_the_fill_color(self):
        state_id = self.env["map.booking.state"].create(
            {
                "name": "Maintenance",
                "code": "maintenance",
                "color": "#6c757d",
            }
        )
        expected = {"fill": "#6c757d", "stroke": "#6c757d", "hover": "#6c757d"}
        self.assertEqual(state_id._get_colors_for_code("maintenance"), expected)
        # Archived states are not offered on the map any more.
        state_id.active = False
        colors = self.env["map.booking.state"]._get_map_colors()
        self.assertNotIn("maintenance", colors)

    @mute_logger("odoo.sql_db")
    def test_code_is_unique(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["map.booking.state"].create(
                {"name": "Duplicate", "code": "free", "color": "#111111"}
            )

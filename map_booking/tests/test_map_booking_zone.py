# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io

from PIL import Image

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MapBookingCommon


@tagged("post_install", "-at_install")
class TestMapBookingZone(MapBookingCommon):
    def test_parse_points(self):
        zone_id = self._create_zone()
        self.assertEqual(
            zone_id._parse_points("1,2 3.5,-4"),
            [(1.0, 2.0), (3.5, -4.0)],
        )

    def test_parse_points_rejects_malformed_values(self):
        zone_id = self._create_zone()
        for points in ("10", "10,10 abc", "10,10 20"):
            with self.assertRaises(ValidationError):
                zone_id._parse_points(points)

    def test_outline_needs_three_corners(self):
        with self.assertRaises(ValidationError):
            self._create_zone(points="10,10 20,20")

    def test_outline_stays_inside_the_image(self):
        buffer = io.BytesIO()
        Image.new("RGB", (200, 100)).save(buffer, format="PNG")
        map_id = self._create_map(image=base64.b64encode(buffer.getvalue()))
        zone_id = self._create_zone(points="0,0 200,0 200,100", map_id=map_id.id)
        with self.assertRaises(ValidationError):
            zone_id.points = "0,0 201,0 200,100"
        with self.assertRaises(ValidationError):
            zone_id.points = "-1,0 200,0 200,100"

    def test_zone_without_resources_has_no_availability(self):
        zone_id = self._create_zone()
        self.assertEqual(zone_id._get_bookable_units(), [])
        self.assertFalse(zone_id._get_availability_state(self._dt(1), self._dt(3)))

    def test_overlap_domain(self):
        zone_id = self._create_zone()
        start, end = self._dt(1), self._dt(3)
        self.assertEqual(
            zone_id._overlap_domain(start, end),
            [("start", "<", end), ("stop", ">", start)],
        )
        # Without an end, or with an end before the start, the stay is the
        # single instant `start`.
        self.assertEqual(
            zone_id._overlap_domain(start),
            [("start", "<=", start), ("stop", ">", start)],
        )
        self.assertEqual(
            zone_id._overlap_domain(start, start),
            [("start", "<=", start), ("stop", ">", start)],
        )

    def test_map_shapes(self):
        zone_id = self._create_zone(self.resource_101_id)
        shape = zone_id._get_map_shapes("free")[0]
        self.assertEqual(shape["id"], f"zone-{zone_id.id}")
        self.assertEqual(shape["zone_id"], zone_id.id)
        self.assertEqual(shape["points"], zone_id.points)
        self.assertEqual(shape["state"], "free")
        self.assertEqual(shape["colors"]["fill"], "#198754")
        # The items themselves come from a booking engine: see the bridges.
        self.assertIn("items", shape)

    def test_zone_without_outline_has_no_shape(self):
        zone_id = self._create_zone(self.resource_101_id, points=False)
        self.assertEqual(zone_id._get_map_shapes("free"), [])

    def test_action_open_form(self):
        zone_id = self._create_zone()
        action = zone_id.action_open_form()
        self.assertEqual(action["res_model"], "map.booking.zone")
        self.assertEqual(action["res_id"], zone_id.id)

# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from odoo.tests import tagged

from .common import MapBookingCommon


@tagged("post_install", "-at_install")
class TestMapBookingMap(MapBookingCommon):
    def test_preview_data(self):
        zone_id = self._create_zone(self.resource_101_id)
        map_id = self._create_map(zones=zone_id)
        data = map_id.preview_data_calculated
        self.assertEqual(data["map_id"], map_id.id)
        self.assertEqual(data["image_url"], map_id._get_image_url())
        self.assertIn(
            f"/web/image/map.booking.map/{map_id.id}/image", data["image_url"]
        )
        self.assertEqual(len(data["shapes"]), 1)
        self.assertEqual(data["shapes"][0]["zone_id"], zone_id.id)
        self.assertEqual([zone["name"] for zone in data["zones"]], [zone_id.name])
        self.assertEqual(
            data["legend"],
            [
                {"label": "Free", "color": "#198754"},
                {"label": "Occupied", "color": "#F58181"},
            ],
        )
        self.assertEqual(data["legend_position"], "bottom_left")

    def test_preview_only_draws_its_own_zones(self):
        zone_1_id = self._create_zone(self.resource_101_id, name="Zone 1")
        map_1_id = self._create_map(name="Map 1", zones=zone_1_id)
        zone_2_id = self._create_zone(self.resource_102_id, name="Zone 2")
        map_2_id = self._create_map(name="Map 2", zones=zone_2_id)
        shapes = map_1_id.preview_data_calculated["shapes"]
        self.assertEqual([shape["zone_id"] for shape in shapes], [zone_1_id.id])
        shapes = map_2_id.preview_data_calculated["shapes"]
        self.assertEqual([shape["zone_id"] for shape in shapes], [zone_2_id.id])

    def test_hidden_legend(self):
        map_id = self._create_map(show_legend=False)
        self.assertEqual(map_id.preview_data_calculated["legend_position"], "none")
        self.assertEqual(map_id.test_preview_data_calculated["legend_position"], "none")

    def test_zone_without_outline_is_not_drawn(self):
        zone_id = self._create_zone(self.resource_101_id, points=False)
        map_id = self._create_map(zones=zone_id)
        self.assertEqual(map_id.preview_data_calculated["shapes"], [])
        self.assertEqual(map_id.test_preview_data_calculated["shapes"], [])

    def test_tested_availability_without_units(self):
        zone_id = self._create_zone()
        map_id = self._create_map(zones=zone_id)
        map_id.write(
            {
                "availability_check_start": date(2026, 7, 1),
                "availability_check_end": date(2026, 7, 3),
            }
        )
        # Nothing to book in the zone: unknown state, neutral color.
        shape = map_id.test_preview_data_calculated["shapes"][0]
        self.assertFalse(shape["state"])
        self.assertIsNone(shape["colors"])

    def test_checked_dates_are_local_midnights(self):
        map_id = self._create_map()
        self.env.user.tz = "Europe/Vienna"
        # 2026-07-01 00:00 in Vienna (UTC+2) is 2026-06-30 22:00 UTC.
        self.assertEqual(
            map_id._to_utc_naive(date(2026, 7, 1)),
            datetime(2026, 6, 30, 22, 0),
        )
        self.assertFalse(map_id._to_utc_naive(False))

    def test_generate_zones_from_resources(self):
        map_id = self._create_map()
        self.env["resource.resource"].create(
            {"name": "Pitch 103", "resource_type": "material"}
        )
        self.env["resource.resource"].create(
            {"name": "Receptionist", "resource_type": "user"}
        )
        map_id.action_generate_zones_from_resources()
        self.assertEqual(
            sorted(map_id.zone_ids.mapped("name")),
            ["Pitch 101", "Pitch 102", "Pitch 103"],
        )
        # Each resource is only offered once.
        map_id.action_generate_zones_from_resources()
        self.assertEqual(len(map_id.zone_ids), 3)

    def test_image_url_of_an_unsaved_map(self):
        map_id = self.env["map.booking.map"].new({"name": "Draft"})
        self.assertFalse(map_id._get_image_url())

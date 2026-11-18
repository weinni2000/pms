# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests import tagged

from .common import ResourceBookingMapBookingCommon


@tagged("post_install", "-at_install")
class TestMapBookingMap(ResourceBookingMapBookingCommon):
    def test_tested_availability_is_colored(self):
        zone_id = self._create_zone(self.resource_101_id)
        map_id = self._create_map(zones=zone_id)
        map_id.write(
            {
                "availability_check_start": date(2026, 7, 1),
                "availability_check_end": date(2026, 7, 3),
            }
        )
        self.assertEqual(
            map_id.test_preview_data_calculated["shapes"][0]["colors"]["fill"],
            "#198754",
        )
        self._create_booking(self.resource_101_id, self._dt(1), self._dt(3))
        map_id.invalidate_recordset(["test_preview_data_calculated"])
        shape = map_id.test_preview_data_calculated["shapes"][0]
        self.assertEqual(shape["state"], "occupied")
        self.assertEqual(shape["colors"]["fill"], "#F58181")

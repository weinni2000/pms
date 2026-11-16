# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.web.tests.test_js import HOOTCommon, unit_test_error_checker


@tagged("post_install", "-at_install")
class TestMapBookingJs(HOOTCommon):
    def test_map_booking_hoot(self):
        """Run the module's own hoot suite (static/tests)."""
        suite_id = self._generate_hash("@map_booking")
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=15000"
            f"&id={suite_id}",
            "",
            "",
            login="admin",
            timeout=1800,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=unit_test_error_checker,
        )

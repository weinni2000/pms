# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import ResourceBookingMapBookingCommon


@tagged("post_install", "-at_install")
class TestMapBookingZone(ResourceBookingMapBookingCommon):
    def test_zone_is_free_without_bookings(self):
        zone_id = self._create_zone(self.resource_101_id)
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_zone_is_occupied_by_an_overlapping_booking(self):
        zone_id = self._create_zone(self.resource_101_id)
        self._create_booking(self.resource_101_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )

    def test_canceled_booking_leaves_the_zone_free(self):
        zone_id = self._create_zone(self.resource_101_id)
        self._create_booking(
            self.resource_101_id, self._dt(2), self._dt(4), canceled=True
        )
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_booking_of_another_resource_leaves_the_zone_free(self):
        zone_id = self._create_zone(self.resource_101_id)
        self._create_booking(self.resource_102_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_zone_with_one_free_resource_stays_free(self):
        resources = self.resource_101_id | self.resource_102_id
        zone_id = self._create_zone(resources)
        self._create_booking(self.resource_101_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )
        # The zone is only occupied once every one of its resources is taken.
        self._create_booking(self.resource_102_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )

    def test_checkout_day_is_not_a_booked_night(self):
        zone_id = self._create_zone(self.resource_101_id)
        self._create_booking(self.resource_101_id, self._dt(2), self._dt(4))
        # A stay starting on the former guest's check-out day is still free.
        self.assertEqual(
            zone_id._get_availability_state(self._dt(4), self._dt(6)), "free"
        )
        # Same for a stay ending the day the booking starts.
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(2)), "free"
        )

    def test_single_instant_check(self):
        zone_id = self._create_zone(self.resource_101_id)
        self._create_booking(self.resource_101_id, self._dt(2), self._dt(4))
        self.assertEqual(zone_id._get_availability_state(self._dt(3, 9)), "occupied")

    def test_map_items_are_the_resources(self):
        zone_id = self._create_zone(self.resource_101_id)
        items = zone_id._get_map_shapes("free")[0]["items"]
        self.assertEqual([item["name"] for item in items], ["Pitch 101"])
        # Items are only pickable while the zone is free.
        self.assertTrue(items[0]["selectable"])
        items = zone_id._get_map_shapes("occupied")[0]["items"]
        self.assertFalse(items[0]["selectable"])

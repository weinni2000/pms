# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from .common import PmsMapBookingCommon


@tagged("post_install", "-at_install")
class TestMapBookingZonePms(PmsMapBookingCommon):
    def test_zone_is_free_without_reservations(self):
        zone_id = self._create_property_zone(self.property_1_id)
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_zone_is_occupied_by_an_overlapping_reservation(self):
        zone_id = self._create_property_zone(self.property_1_id)
        self._create_reservation(self.property_1_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )

    def test_cancelled_reservation_leaves_the_zone_free(self):
        zone_id = self._create_property_zone(self.property_1_id)
        stage_cancelled_id = self.env.ref("pms_sale.pms_stage_cancelled")
        self._create_reservation(
            self.property_1_id,
            self._dt(2),
            self._dt(4),
            stage_id=stage_cancelled_id,
        )
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_draft_reservation_leaves_the_zone_free(self):
        zone_id = self._create_property_zone(self.property_1_id)
        stage_new_id = self.env.ref("pms_sale.pms_stage_new")
        self._create_reservation(
            self.property_1_id, self._dt(2), self._dt(4), stage_id=stage_new_id
        )
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_reservation_of_another_property_leaves_the_zone_free(self):
        zone_id = self._create_property_zone(self.property_1_id)
        self._create_reservation(self.property_2_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )

    def test_zone_with_one_free_property_stays_free(self):
        properties = self.property_1_id | self.property_2_id
        zone_id = self._create_property_zone(properties)
        self._create_reservation(self.property_1_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )
        # The zone is only occupied once every one of its properties is taken.
        self._create_reservation(self.property_2_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )

    def test_checkout_day_is_not_a_booked_night(self):
        zone_id = self._create_property_zone(self.property_1_id)
        self._create_reservation(self.property_1_id, self._dt(2), self._dt(4))
        # A stay starting on the former guest's check-out day is still free.
        self.assertEqual(
            zone_id._get_availability_state(self._dt(4), self._dt(6)), "free"
        )
        # Same for a stay ending the day the reservation starts.
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(2)), "free"
        )

    def test_single_instant_check(self):
        zone_id = self._create_property_zone(self.property_1_id)
        self._create_reservation(self.property_1_id, self._dt(2), self._dt(4))
        self.assertEqual(zone_id._get_availability_state(self._dt(3, 9)), "occupied")

    def test_map_items_are_the_properties(self):
        zone_id = self._create_property_zone(self.property_1_id)
        items = zone_id._get_map_shapes("free")[0]["items"]
        self.assertEqual([item["name"] for item in items], ["Pitch 101"])

    def test_zone_holds_the_properties_of_its_tags(self):
        tag_id = self.env["pms.tag"].create({"name": "Map Booking Test Tag"})
        self.property_2_id.tag_ids = [Command.link(tag_id.id)]
        zone_id = self._create_property_zone(
            self.property_1_id, property_tag_ids=[Command.set(tag_id.ids)]
        )
        units = zone_id._get_bookable_units(self._dt(1), self._dt(3))
        self.assertEqual(
            [unit for unit, _busy in units], [self.property_1_id, self.property_2_id]
        )
        # Like a picked one, a tagged property keeps the zone free until it is
        # taken too.
        self._create_reservation(self.property_1_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "free"
        )
        self._create_reservation(self.property_2_id, self._dt(2), self._dt(4))
        self.assertEqual(
            zone_id._get_availability_state(self._dt(1), self._dt(3)), "occupied"
        )

# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.map_booking_pms_bridge.tests.common import PmsMapBookingCommon


@tagged("post_install", "-at_install")
class TestMapBookingWebsite(PmsMapBookingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.property_1_id | cls.property_2_id).is_published = True
        cls.zone_1_id = cls._create_property_zone(cls.property_1_id, "Pitch 101")
        cls.zone_2_id = cls._create_property_zone(cls.property_2_id, "Pitch 102")
        cls.map_id = cls._create_map(cls.zone_1_id | cls.zone_2_id, name="B Map")

    @classmethod
    def _create_property_zone(cls, property_id, name):
        return cls.env["map.booking.zone"].create(
            {
                "name": name,
                "points": "10,10 110,10 110,60 10,60",
                "property_ids": [Command.set(property_id.ids)],
            }
        )

    def _items(self, data, zone_id):
        shape = next(
            shape for shape in data["shapes"] if shape["zone_id"] == zone_id.id
        )
        return shape

    def test_map_of_the_property(self):
        self.assertEqual(self.property_1_id._get_map_booking_website_map(), self.map_id)
        # The first map in the maps' order wins.
        first_map_id = self._create_map(
            self._create_property_zone(self.property_1_id, "Pitch 101"),
            name="A Map",
        )
        self.assertEqual(
            self.property_1_id._get_map_booking_website_map(), first_map_id
        )
        self.assertEqual(self.property_2_id._get_map_booking_website_map(), self.map_id)

    def test_map_through_property_tag(self):
        tag_id = self.env["pms.tag"].create({"name": "Lake side"})
        property_id = self._create_property("Pitch 103")
        property_id.tag_ids = tag_id
        self.assertFalse(property_id._get_map_booking_website_map())
        self.zone_2_id.property_tag_ids = tag_id
        self.assertEqual(property_id._get_map_booking_website_map(), self.map_id)

    def test_zones_follow_the_stay(self):
        self._create_reservation(self.property_2_id, self._dt(2), self._dt(4))
        data = self.map_id._get_pms_website_data(self._dt(1), self._dt(3))
        shape_1 = self._items(data, self.zone_1_id)
        shape_2 = self._items(data, self.zone_2_id)
        self.assertEqual(shape_1["state"], "free")
        self.assertTrue(shape_1["items"][0]["selectable"])
        self.assertEqual(
            shape_1["items"][0]["website_url"], self.property_1_id.website_url
        )
        self.assertEqual(shape_2["state"], "occupied")
        self.assertFalse(shape_2["items"][0]["selectable"])
        self.assertIn(
            f"/map_booking_pms_website_sale/map/{self.map_id.id}/image",
            data["image_url"],
        )

    def test_no_stay_no_state(self):
        data = self.map_id._get_pms_website_data()
        shape_1 = self._items(data, self.zone_1_id)
        self.assertFalse(shape_1["state"])
        self.assertTrue(shape_1["items"][0]["selectable"])

    def test_unpublished_property_cannot_be_picked(self):
        self.property_2_id.is_published = False
        data = self.map_id._get_pms_website_data()
        self.assertFalse(self._items(data, self.zone_2_id)["items"][0]["selectable"])

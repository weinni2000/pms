# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import Command
from odoo.tests.common import TransactionCase


class MapBookingCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.resource_101_id = cls.env["resource.resource"].create(
            {"name": "Pitch 101", "resource_type": "material"}
        )
        cls.resource_102_id = cls.env["resource.resource"].create(
            {"name": "Pitch 102", "resource_type": "material"}
        )
        cls.state_free_id = cls.env.ref("map_booking.map_booking_state_free")
        cls.state_occupied_id = cls.env.ref("map_booking.map_booking_state_occupied")

    @classmethod
    def _create_zone(cls, resources=None, **values):
        resources = resources or cls.env["resource.resource"]
        values.setdefault("name", "Zone")
        values.setdefault("points", "10,10 110,10 110,60 10,60")
        values["resource_ids"] = [Command.set(resources.ids)]
        return cls.env["map.booking.zone"].create(values)

    @classmethod
    def _create_map(cls, zones=None, **values):
        values.setdefault("name", "Map")
        values.setdefault("image", b"ZmFrZSBpbWFnZQ==")
        map_id = cls.env["map.booking.map"].create(values)
        for zone_id in zones or cls.env["map.booking.zone"]:
            zone_id.map_id = map_id
        return map_id

    @classmethod
    def _dt(cls, day, hour=14):
        return datetime(2026, 7, day, hour, 0, 0)

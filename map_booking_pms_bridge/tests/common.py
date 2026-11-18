# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.map_booking.tests.common import MapBookingCommon


class PmsMapBookingCommon(MapBookingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner_id = cls.env["res.partner"].create({"name": "Owner"})
        cls.property_1_id = cls._create_property("Pitch 101")
        cls.property_2_id = cls._create_property("Pitch 102")
        cls.stage_confirmed_id = cls.env.ref("pms_sale.pms_stage_confirmed")

    @classmethod
    def _create_property(cls, name):
        return cls.env["pms.property"].create(
            {
                "name": name,
                "owner_id": cls.owner_id.id,
                "tz": "UTC",
                "min_nights": 1,
                "max_nights": 30,
            }
        )

    @classmethod
    def _create_reservation(cls, property_id, start, stop, stage_id=None):
        return cls.env["pms.reservation"].create(
            {
                "property_id": property_id.id,
                "start": start,
                "stop": stop,
                "stage_id": (stage_id or cls.stage_confirmed_id).id,
            }
        )

    @classmethod
    def _create_property_zone(cls, property_id, **values):
        values.setdefault("name", "Zone")
        values.setdefault("points", "10,10 110,10 110,60 10,60")
        values["property_ids"] = [Command.set(property_id.ids)]
        return cls.env["map.booking.zone"].create(values)

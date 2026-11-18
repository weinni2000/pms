# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.map_booking.tests.common import MapBookingCommon


class ResourceBookingMapBookingCommon(MapBookingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_id = cls.env["res.partner"].create({"name": "Guest"})
        cls.booking_type_id = cls.env["resource.booking.type"].create(
            {
                "name": "Stay",
                "duration": 1.0,
                "slot_duration": 1.0,
            }
        )

    @classmethod
    def _create_booking(cls, resources, start, stop, canceled=False):
        combination_id = cls.env["resource.booking.combination"].create(
            {"resource_ids": [Command.set(resources.ids)]}
        )
        booking_id = cls.env["resource.booking"].create(
            {
                "type_id": cls.booking_type_id.id,
                "combination_id": combination_id.id,
                "combination_auto_assign": False,
                "partner_ids": [Command.set(cls.partner_id.ids)],
                "start": start,
                "duration": (stop - start).total_seconds() / 3600,
            }
        )
        if canceled:
            # Canceling a booking archives it.
            booking_id.active = False
        return booking_id

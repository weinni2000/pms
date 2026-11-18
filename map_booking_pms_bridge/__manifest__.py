# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Map Booking - PMS Bridge",
    "summary": "Color map booking zones from PMS reservations",
    "version": "19.0.1.0.1",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/pms",
    "author": "mytime.click, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "map_booking",
        "pms_sale",
    ],
    "data": [
        "security/res_groups.xml",
        "views/map_booking_zone_views.xml",
        "views/map_booking_map_views.xml",
    ],
    "demo": [
        "demo/pms_property_demo.xml",
        "demo/pms_reservation_demo.xml",
        "demo/map_booking_zone_demo.xml",
    ],
    "installable": True,
}

# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Map Booking",
    "summary": "Interactive map of bookable resources with live availability",
    "version": "19.0.1.0.1",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/pms",
    "author": "mytime.click, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "map_widget",
        "resource",
    ],
    "data": [
        "security/map_booking_security.xml",
        "security/ir.model.access.csv",
        "data/map_booking_state_data.xml",
        # The map views define the root menu the other menus hang from.
        "views/map_booking_map_views.xml",
        "views/map_booking_zone_views.xml",
        "views/map_booking_state_views.xml",
    ],
    "demo": [
        "demo/resource_resource_demo.xml",
        "demo/map_booking_map_demo.xml",
        "demo/map_booking_zone_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "map_booking/static/src/backend/**/*",
        ],
        "web.assets_unit_tests": [
            "map_booking/static/tests/**/*",
        ],
    },
    "installable": True,
}

# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Map Booking - PMS Website Sale",
    "summary": "Show the map of a property in its website booking dialog",
    "version": "19.0.1.0.2",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/pms",
    "author": "mytime.click, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "map_booking_pms_bridge",
        "pms_website_sale",
    ],
    "data": [
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "map_booking_pms_website_sale/static/src/frontend/**/*",
        ],
    },
    "installable": True,
}

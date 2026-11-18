# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Map Booking - Hotel Reservation",
    "summary": "Pick the rooms of a hotel reservation on the map",
    "version": "19.0.1.0.4",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/pms",
    "author": "mytime.click, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "map_booking_hotel_bridge",
    ],
    "data": [
        "views/hotel_reservation_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "map_booking_hotel_reservation/static/src/backend/**/*",
        ],
    },
    "installable": True,
}

# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Map Booking - Hotel Bridge",
    "summary": "Color map booking zones from hotel reservations and folios",
    "version": "19.0.1.0.1",
    "development_status": "Beta",
    "category": "Appointments",
    "website": "https://github.com/OCA/pms",
    "author": "mytime.click, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "map_booking",
        "hotel_reservation",
    ],
    "data": [
        "security/res_groups.xml",
        "views/map_booking_zone_views.xml",
        "views/map_booking_map_views.xml",
    ],
    "demo": [
        "demo/hotel_room_demo.xml",
        "demo/hotel_reservation_demo.xml",
        "demo/map_booking_zone_demo.xml",
    ],
    "installable": True,
}

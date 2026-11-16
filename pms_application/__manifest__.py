# Copyright 2026 mytime.click
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "PMS - Application",
    "summary": "Install every module of the Property Management System at once",
    "version": "19.0.1.0.1",
    "development_status": "Beta",
    "category": "Generic Modules/Property Management System",
    "website": "https://github.com/OCA/pms",
    "author": "mytime.click, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    "depends": [
        "map_booking",
        "map_booking_pms_bridge",
        "map_widget",
        "pms_account",
        "pms_account_asset",
        "pms_base",
        "pms_contract",
        "pms_crm",
        "pms_project",
        "pms_purchase",
        "pms_sale",
        "pms_stock",
        "pms_website",
        "pms_website_sale",
    ],
}

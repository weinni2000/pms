# Copyright 2026 mytime.click
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Map Widget",
    "summary": "Reusable map widget to draw and pick zones on an image",
    "version": "19.0.1.0.1",
    "development_status": "Beta",
    "category": "Technical",
    "website": "https://github.com/OCA/pms",
    "author": "mytime.click, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "map_widget/static/src/components/**/*",
            "map_widget/static/src/scss/map_widget.scss",
        ],
        "web.assets_frontend": [
            "map_widget/static/src/components/**/*",
            "map_widget/static/src/js/**/*",
            "map_widget/static/src/scss/map_widget.scss",
        ],
        "web.assets_unit_tests": [
            "map_widget/static/tests/**/*",
        ],
    },
    "installable": True,
}

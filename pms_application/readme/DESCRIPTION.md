Installs the complete Property Management System in one step.

The `pms_` modules build on each other, so a fresh database needs a hand-picked
list of modules before the suite is usable. This metapackage depends on every
module of the repository, so installing it once installs the whole suite,
together with the modules the individual apps pull in from other OCA
repositories (`contract`, `account_asset_management`, `web_timeline`).

It adds no data model, no view and no menu of its own: it is the entry point
that turns the repository into a single application.

Bundled modules:

- `pms_base` — properties, rooms, services and amenities
- `pms_account` — accounting on properties
- `pms_account_asset` — asset management on properties
- `pms_contract` — contracts on properties
- `pms_crm` — leads on properties
- `pms_project` — projects and tasks on properties
- `pms_purchase` — property on purchase order lines
- `pms_sale` — reservations
- `pms_stock` — stock content of a property
- `pms_website` — properties on the website
- `pms_website_sale` — online booking
- `map_widget` — reusable map widget
- `map_booking` — interactive map of bookable resources
- `map_booking_pms_bridge` — color the map zones from PMS reservations

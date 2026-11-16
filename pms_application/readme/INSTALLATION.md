The bundled modules depend on modules from other repositories, so these have to
be in the addons path before the application can be installed:

- `contract` from [OCA/contract](https://github.com/OCA/contract)
- `account_asset_management` from
  [OCA/account-financial-tools](https://github.com/OCA/account-financial-tools)
- `web_timeline` from [OCA/web](https://github.com/OCA/web)

Installing `pms_application` installs all of them in one go; there is no need to
install the `pms_` modules one by one.

The separate `map_booking_resource_booking_bridge` module additionally needs
`resource_booking` from [OCA/calendar](https://github.com/OCA/calendar).

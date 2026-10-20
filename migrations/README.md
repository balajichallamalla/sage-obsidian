# Migrations

`NNN_<name>.py` scripts run in order by `upgrade` when a vault's `schema_version` is below NNN. Each
runs with the vault as the working directory, must be idempotent, and must not touch `raw/`. None yet:
schema version 1 is the first.

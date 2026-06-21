# guardium_notes_dbtraffic

Universal application traffic generator framework.

## Goals

- scenario-driven traffic generation
- pluggable database adapters
- reusable workload engine
- configurable data generation
- structured execution reports

## Current implemented scope

- YAML configuration
- CLI entrypoint
- scenario registry
- PostgreSQL adapter
- Oracle adapter
- schema deploy and cleanup for `micro_payments`
- seed data generation for `micro_payments`
- runtime application flow for `micro_payments`
- first scenario: `micro_payments`

## Install

```bash
pip install -e .
```

## Configuration

Example configuration file:

```yaml
database:
  type: postgres
  host: 127.0.0.1
  port: 5432
  database: appdb
  user: appuser
  password: secret

workload:
  duration_seconds: 60
  virtual_users: 2
  think_time_ms: 250

scenario:
  name: micro_payments
  options:
    locale: pl_PL
    seed_customers: 100
    app_users:
      - appuser1
      - appuser2
    admin_users:
      - adminuser1
    default_password: Guardium123!
```

## Commands

List scenarios:

```bash
guardium-notes-dbtraffic list-scenarios
```

Validate config:

```bash
guardium-notes-dbtraffic --config config/example.yaml validate-config
```

Deploy schema:

```bash
guardium-notes-dbtraffic --config config/example.yaml deploy-schema
```

Seed data:

```bash
guardium-notes-dbtraffic --config config/example.yaml seed-data
```

Run application traffic:

```bash
guardium-notes-dbtraffic --config config/example.yaml run
```

Cleanup schema:

```bash
guardium-notes-dbtraffic --config config/example.yaml cleanup-schema
```

## Notes

Current runtime implements the main application-side flow for the original `micro_payments` model:
- `get_customer_info`
- `add_customer`
- `add_credit_card`
- `buy_feature`

The project preserves the original business naming model:
- schema/user model based on `game`
- application role model based on `appusers`
- admin role model based on `adminusers`

# Made with Bob
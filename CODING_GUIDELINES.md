# Coding Guidelines - guardium_notes_dbtraffic

## Architecture Principles

### Separation of Concerns
- **config.py**: YAML loading → models
- **models.py**: dataclasses only, no logic
- **db.py**: database adapters, connection management
- **registry.py**: scenario registration and lookup
- **cli.py**: argument parsing, command dispatch
- **micro_payments_*.py**: scenario-specific implementation

### Adapter Pattern
```python
class DatabaseAdapter:
    def connect(self) -> None: ...
    def execute(self, sql: str) -> QueryResult: ...
    def close(self) -> None: ...
```
Each database type (PostgresAdapter, OracleAdapter) implements the interface.

### Registry Pattern
```python
registry = ScenarioRegistry()
registry.register(MicroPaymentsScenario())
scenario = registry.get("micro_payments")
```
Enables pluggable scenarios without modifying core code.

## Code Style

### Minimize Code
- Extract common patterns into reusable functions
- Use dataclasses for data structures
- Avoid duplication between database adapters

### Minimize Comments
- Code should be self-documenting
- Use descriptive names: `_customer_id_sql()` not `_get_cust()`
- Only comment complex business logic or non-obvious decisions

### Type Hints
```python
def load_config(path: Path) -> AppConfig:
def execute(self, sql: str) -> QueryResult:
```
Always use type hints for function signatures.

### Imports
```python
from __future__ import annotations  # Enable forward references
from typing import Any, List, Tuple
```
Use `__all__` to control public API.

## Database Abstraction

### SQL Generation
Keep database-specific SQL in dedicated functions:
```python
def _customer_id_sql(database_type: str) -> str:
    if database_type == "oracle":
        return "SELECT ... ORDER BY DBMS_RANDOM.VALUE FETCH FIRST 1 ROWS ONLY"
    return "SELECT ... ORDER BY random() LIMIT 1"
```

### Connection Management
```python
def connect(self) -> None:
    if self.connection is not None:
        return  # Already connected
    # Create connection
```
Lazy connection, explicit close.

### Batch Execution
```python
def execute_batch(self, statements: list[str]) -> None:
    for statement in statements:
        self.execute(statement)
```
Reuse single execute method.

## Scenario Implementation

### File Organization
- `micro_payments_constants.py`: constants
- `micro_payments_defaults.py`: default values
- `micro_payments_data.py`: data generation helpers
- `micro_payments_schema.py`: DDL statements
- `micro_payments_seed.py`: seed data generation
- `micro_payments_runtime.py`: traffic generation logic
- `scenarios_micro_payments.py`: scenario registration

### Configuration Access
```python
def _scenario_option(self, key: str, default: Any) -> Any:
    return self.config.scenario.options.get(key, default)

locale = str(self._scenario_option("locale", "pl_PL"))
```
Centralized option access with defaults.

### SQL Escaping
```python
def _escape_sql_text(value: str) -> str:
    return value.replace("'", "''")
```
Always escape user-generated strings in SQL.

## CLI Design

### Command Structure
```bash
guardium-notes-dbtraffic [--config FILE] [--dry-run] COMMAND [OPTIONS]
```

### Commands
- `list-scenarios`: no config needed
- `validate-config`: load and validate
- `deploy-schema`: DDL execution
- `seed-data`: DML execution
- `run`: traffic generation
- `cleanup-schema`: cleanup DDL

### Dry Run
```python
if args.dry_run:
    _print_execution_plan(...)
    return
```
Print plan without execution.

## Refactoring Opportunities

### Extract Common SQL Patterns
```python
def _random_row_sql(database_type: str, table: str, column: str) -> str:
    if database_type == "oracle":
        return f"SELECT {column} FROM {table} ORDER BY DBMS_RANDOM.VALUE FETCH FIRST 1 ROWS ONLY"
    return f"SELECT {column} FROM {table} ORDER BY random() LIMIT 1"
```

### Consolidate User Management
```python
def _get_users(self, user_type: str) -> list[str]:
    key = f"{user_type}_users"
    default = ["appuser1"] if user_type == "app" else ["adminuser1"]
    return [str(u) for u in self._scenario_option(key, default)]
```

### Parameterize SQL Generation
Instead of separate functions for each insert, use:
```python
def _build_insert_sql(table: str, columns: dict[str, Any]) -> str:
    cols = ", ".join(columns.keys())
    vals = ", ".join(_format_value(v) for v in columns.values())
    return f"INSERT INTO {table} ({cols}) VALUES ({vals})"
```

## Testing Strategy

### Unit Tests
- Test SQL generation functions with different database types
- Test configuration loading with various YAML structures
- Test adapter connection/close lifecycle

### Integration Tests
- Test full workflow: deploy → seed → run → cleanup
- Test with real database instances (Docker)
- Verify data integrity after operations

## Extension Points

### Adding New Database
1. Create `NewDbAdapter(DatabaseAdapter)` in `db.py`
2. Implement: `connect()`, `close()`, `execute()`, `schema_exists()`
3. Add to `build_adapter()` factory
4. Create schema SQL in `micro_payments_schema.py`

### Adding New Scenario
1. Create `scenarios_new_scenario.py`
2. Implement `Scenario` interface
3. Create schema/seed/runtime modules
4. Register in `registry.py`

### Adding New Operation
1. Add to operations list in `run_micro_payments()`
2. Create SQL generation function
3. Add stats counter
4. Update CLI output

## Questions to Ask

Before implementing:
- Can this be extracted into a reusable function?
- Does this duplicate existing code?
- Is there a simpler way to achieve this?
- Should this be configurable?
- Does this work for all supported databases?

## Best Practices

### DO
- Use dataclasses for data structures
- Use type hints everywhere
- Extract database-specific logic
- Reuse existing patterns
- Keep functions small and focused
- Use descriptive variable names

### DON'T
- Hardcode values (use config)
- Duplicate SQL generation logic
- Mix business logic with infrastructure
- Use bare `except:` clauses
- Leave connections open
- Ignore type hints

## Performance Considerations

### Connection Pooling
Current implementation: single connection per adapter.
Future: connection pool for multi-threaded workloads.

### Batch Operations
Use `execute_batch()` for multiple statements.
Consider transaction batching for better performance.

### Think Time
```python
sleep(max(think_time_ms, 0) / 1000.0)
```
Configurable delay between operations to simulate real traffic.

## Security

### SQL Injection Prevention
Always escape user input:
```python
value = _escape_sql_text(user_input)
sql = f"INSERT INTO table VALUES ('{value}')"
```

### Password Management
Store passwords in config file (not in code).
Consider environment variables for sensitive data.

### Connection Security
Support SSL/TLS connections in adapter configuration.

---

**Remember**: Minimize code, minimize comments, ask when unclear, suggest better approaches.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from guardium_notes_dbtraffic.micro_payments_constants import SCHEMA_NAME
from guardium_notes_dbtraffic.micro_payments_schema import (
    oracle_cleanup_sql,
    oracle_deploy_sql,
    postgres_cleanup_sql,
    postgres_deploy_sql,
)
from guardium_notes_dbtraffic.micro_payments_seed import build_seed_sql
from guardium_notes_dbtraffic.models import AppConfig


@dataclass(slots=True)
class QueryResult:
    rows: list[tuple[Any, ...]]


class DatabaseAdapter:
    name = "base"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.connection: Any | None = None

    def connect(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def execute(self, sql: str) -> QueryResult:
        raise NotImplementedError

    def execute_scalar(self, sql: str) -> Any:
        rows = self.execute(sql).rows
        if not rows:
            return None
        return rows[0][0]

    def execute_batch(self, statements: list[str]) -> None:
        for statement in statements:
            self.execute(statement)

    def schema_exists(self, schema_name: str) -> bool:
        raise NotImplementedError

    def _scenario_option(self, key: str, default: Any) -> Any:
        return self.config.scenario.options.get(key, default)

    def _app_users(self) -> list[str]:
        users = self._scenario_option("app_users", ["appuser1", "appuser2"])
        return [str(user) for user in users]

    def _admin_users(self) -> list[str]:
        users = self._scenario_option("admin_users", ["adminuser1"])
        return [str(user) for user in users]

    def _default_password(self) -> str:
        return str(self._scenario_option("default_password", self.config.database.password or "Guardium123!"))

    def seed_micro_payments_data(self) -> None:
        locale = str(self._scenario_option("locale", "pl_PL"))
        seed_customers = int(self._scenario_option("seed_customers", 100))
        statements = build_seed_sql(
            database_type=self.config.database.type,
            locale=locale,
            seed_customers=seed_customers,
        )
        self.execute_batch(statements)

    def deploy_micro_payments_schema(self) -> None:
        raise NotImplementedError

    def cleanup_micro_payments_schema(self) -> None:
        raise NotImplementedError


class PostgresAdapter(DatabaseAdapter):
    name = "postgres"

    def connect(self) -> None:
        if self.connection is not None:
            return
        import psycopg2

        self.connection = psycopg2.connect(
            host=self.config.database.host,
            port=self.config.database.port,
            dbname=self.config.database.database,
            user=self.config.database.user,
            password=self.config.database.password,
        )
        self.connection.autocommit = True

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute(self, sql: str) -> QueryResult:
        self.connect()
        assert self.connection is not None
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            rows: list[tuple[Any, ...]] = []
            if cursor.description is not None:
                rows = list(cursor.fetchall())
            return QueryResult(rows=rows)

    def schema_exists(self, schema_name: str) -> bool:
        result = self.execute_scalar(
            "SELECT EXISTS (SELECT 1 FROM information_schema.schemata "
            f"WHERE schema_name = '{schema_name}')"
        )
        return bool(result)

    def deploy_micro_payments_schema(self) -> None:
        statements = postgres_deploy_sql(
            app_users=self._app_users(),
            admin_users=self._admin_users(),
            default_password=self._default_password(),
        )
        self.execute_batch(statements)

    def cleanup_micro_payments_schema(self) -> None:
        statements = postgres_cleanup_sql(
            app_users=self._app_users(),
            admin_users=self._admin_users(),
        )
        self.execute_batch(statements)


class OracleAdapter(DatabaseAdapter):
    name = "oracle"

    def connect(self) -> None:
        if self.connection is not None:
            return
        import oracledb

        dsn = oracledb.makedsn(
            self.config.database.host,
            self.config.database.port,
            service_name=self.config.database.database,
        )
        self.connection = oracledb.connect(
            user=self.config.database.user,
            password=self.config.database.password,
            dsn=dsn,
        )
        self.connection.autocommit = True

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute(self, sql: str) -> QueryResult:
        self.connect()
        assert self.connection is not None
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            rows: list[tuple[Any, ...]] = []
            if cursor.description is not None:
                rows = list(cursor.fetchall())
            return QueryResult(rows=rows)

    def schema_exists(self, schema_name: str) -> bool:
        result = self.execute_scalar(
            "SELECT COUNT(*) FROM all_users "
            f"WHERE username = '{schema_name.upper()}'"
        )
        return int(result or 0) > 0

    def deploy_micro_payments_schema(self) -> None:
        statements = oracle_deploy_sql(
            app_users=self._app_users(),
            admin_users=self._admin_users(),
            default_password=self._default_password(),
        )
        self.execute_batch(statements)

    def cleanup_micro_payments_schema(self) -> None:
        statements = oracle_cleanup_sql(
            app_users=self._app_users(),
            admin_users=self._admin_users(),
        )
        self.execute_batch(statements)


def build_adapter(config: AppConfig) -> DatabaseAdapter:
    if config.database.type == "postgres":
        return PostgresAdapter(config)
    if config.database.type == "oracle":
        return OracleAdapter(config)
    raise ValueError(f"Unsupported database type: {config.database.type}")

# Made with Bob

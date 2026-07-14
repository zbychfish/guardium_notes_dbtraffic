from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple

from guardium_notes_dbtraffic.micro_payments_constants import SCHEMA_NAME
from guardium_notes_dbtraffic.micro_payments_schema import (
    informix_cleanup_sql,
    informix_deploy_sql,
    oracle_cleanup_sql,
    oracle_deploy_sql,
    postgres_cleanup_sql,
    postgres_deploy_sql,
)
from guardium_notes_dbtraffic.micro_payments_seed import build_seed_sql
from guardium_notes_dbtraffic.models import AppConfig


@dataclass
class QueryResult:
    rows: List[Tuple[Any, ...]]


class DatabaseAdapter:
    name = "base"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.connection: Any | None = None
        self.show_sql = False

    def connect(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def execute(self, sql: str) -> QueryResult:
        if self.show_sql:
            print(f"[SQL] {sql}")
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
        if self.show_sql:
            print(f"[SQL] {sql}")
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
        if self.show_sql:
            print(f"[SQL] {sql}")
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


class InformixAdapter(DatabaseAdapter):
    name = "informix"

    @staticmethod
    def _find_jdbc_jars() -> list[str]:
        import glob
        import os
        candidates = [
            "/opt/guardium_tz_bootcamp_automation/upload/source_files/informix/jdbc-15.0.1.3.jar",
            "/opt/ibm/informix/jdbc/lib/ifxjdbc.jar",
            "/opt/informix/jdbc/lib/ifxjdbc.jar",
            "/usr/informix/jdbc/lib/ifxjdbc.jar",
        ]
        informix_dir = os.environ.get("INFORMIXDIR", "")
        if informix_dir:
            candidates.insert(0, os.path.join(informix_dir, "jdbc", "lib", "ifxjdbc.jar"))
        jdbc = next((p for p in candidates if os.path.isfile(p)), None)
        if not jdbc:
            raise FileNotFoundError(
                "ifxjdbc.jar not found. Set jdbc_jar in scenario options or install Informix JDBC driver."
            )
        jars = [jdbc]
        for bson in glob.glob(os.path.join(os.path.dirname(jdbc), "bson*.jar")):
            jars.append(bson)
        return jars

    def connect(self) -> None:
        if self.connection is not None:
            return
        import jaydebeapi

        jdbc_jar_option = str(self._scenario_option("jdbc_jar", ""))
        jdbc_jars: list[str] = jdbc_jar_option.split(":") if jdbc_jar_option else self._find_jdbc_jars()
        server = self.config.database.server or self.config.database.database
        url = (
            f"jdbc:informix-sqli://{self.config.database.host}:{self.config.database.port}"
            f"/{self.config.database.database}:INFORMIXSERVER={server}"
        )
        self.connection = jaydebeapi.connect(
            "com.informix.jdbc.IfxDriver",
            url,
            [self.config.database.user, self.config.database.password],
            jdbc_jars,
        )
        self.connection.jconn.setAutoCommit(True)

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def execute(self, sql: str) -> QueryResult:
        if self.show_sql:
            print(f"[SQL] {sql}")
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
            f"SELECT COUNT(*) FROM systables WHERE tabtype = 'T' AND owner = '{schema_name.lower()}'"
        )
        return int(result or 0) > 0

    def deploy_micro_payments_schema(self) -> None:
        statements = informix_deploy_sql(
            app_users=self._app_users(),
            admin_users=self._admin_users(),
            default_password=self._default_password(),
        )
        for statement in statements:
            try:
                self.execute(statement)
            except Exception as exc:
                msg = str(exc)
                if any(s in msg for s in ("already exists", "duplicate table name", "User does not exist", "USERMAPPING")):
                    pass  # table already exists or user/grant not supported – idempotent deploy
                else:
                    raise

    def cleanup_micro_payments_schema(self) -> None:
        for table in ["transactions", "credit_cards", "customers", "features", "extras"]:
            count = self.execute_scalar(
                f"SELECT COUNT(*) FROM systables WHERE tabname = '{table}' AND tabtype = 'T'"
            )
            if int(count or 0) > 0:
                self.execute(f"DROP TABLE {table}")


def build_adapter(config: AppConfig) -> DatabaseAdapter:
    if config.database.type == "postgres":
        return PostgresAdapter(config)
    if config.database.type == "oracle":
        return OracleAdapter(config)
    if config.database.type == "informix":
        return InformixAdapter(config)
    raise ValueError(f"Unsupported database type: {config.database.type}")

# Made with Bob

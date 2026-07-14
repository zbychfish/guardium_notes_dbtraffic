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
    def _setup_library_path() -> None:
        import importlib.util
        import os

        lib = os.environ.get("LD_LIBRARY_PATH", "")

        # Locate onedb-odbc-driver bundled with IfxPy in site-packages
        spec = importlib.util.find_spec("IfxPy")
        if spec and spec.origin:
            site_packages = os.path.dirname(os.path.dirname(spec.origin))
            driver_lib = os.path.join(site_packages, "onedb-odbc-driver", "lib")
            for sub in ("", "cli", "esql", os.path.join("client", "csm")):
                path = os.path.join(driver_lib, sub) if sub else driver_lib
                if os.path.isdir(path) and path not in lib:
                    lib = f"{path}:{lib}"

        # Also add INFORMIXDIR libs if available
        informix_dir = os.environ.get("INFORMIXDIR", "")
        if not informix_dir:
            import subprocess
            try:
                result = subprocess.run(
                    ["su", "-", "informix", "-c", "echo $INFORMIXDIR"],
                    capture_output=True, text=True, timeout=5,
                )
                informix_dir = result.stdout.strip()
                if informix_dir:
                    os.environ["INFORMIXDIR"] = informix_dir
            except Exception:
                pass
        for sub in ("lib", "lib/esql"):
            path = f"{informix_dir}/{sub}"
            if informix_dir and os.path.isdir(path) and path not in lib:
                lib = f"{path}:{lib}"

        os.environ["LD_LIBRARY_PATH"] = lib

    def connect(self) -> None:
        if self.connection is not None:
            return
        self._setup_library_path()
        import IfxPy

        server = self.config.database.server or self.config.database.database
        conn_str = (
            f"SERVER={server};"
            f"HOST={self.config.database.host};"
            f"SERVICE={self.config.database.port};"
            f"DATABASE={self.config.database.database};"
            f"UID={self.config.database.user};"
            f"PWD={self.config.database.password};"
            "PROTOCOL=onsoctcp;"
        )
        self.connection = IfxPy.connect(conn_str, "", "")

    def close(self) -> None:
        if self.connection is not None:
            import IfxPy
            IfxPy.close(self.connection)
            self.connection = None

    def execute(self, sql: str) -> QueryResult:
        if self.show_sql:
            print(f"[SQL] {sql}")
        self.connect()
        assert self.connection is not None
        import IfxPy
        stmt = IfxPy.exec_immediate(self.connection, sql)
        rows: list[tuple[Any, ...]] = []
        if stmt and IfxPy.num_fields(stmt) > 0:
            row = IfxPy.fetch_tuple(stmt)
            while row is not False:
                rows.append(tuple(row))
                row = IfxPy.fetch_tuple(stmt)
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
        self.execute_batch(statements)

    def cleanup_micro_payments_schema(self) -> None:
        statements = informix_cleanup_sql(
            app_users=self._app_users(),
            admin_users=self._admin_users(),
        )
        for statement in statements:
            try:
                self.execute(statement)
            except Exception as exc:
                msg = str(exc)
                if any(code in msg for code in ("-206", "-951", "-25596", "-26732")):
                    pass  # table/user does not exist – safe to ignore during cleanup
                else:
                    raise


def build_adapter(config: AppConfig) -> DatabaseAdapter:
    if config.database.type == "postgres":
        return PostgresAdapter(config)
    if config.database.type == "oracle":
        return OracleAdapter(config)
    if config.database.type == "informix":
        return InformixAdapter(config)
    raise ValueError(f"Unsupported database type: {config.database.type}")

# Made with Bob

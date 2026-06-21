from __future__ import annotations

from pathlib import Path

import yaml

from guardium_notes_dbtraffic.models import AppConfig, DatabaseConfig, ScenarioConfig, WorkloadConfig

__all__ = ["load_config"]


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as file_handle:
        raw_config = yaml.safe_load(file_handle) or {}

    database_raw = raw_config.get("database", {})
    workload_raw = raw_config.get("workload", {})
    scenario_raw = raw_config.get("scenario", {})

    database = DatabaseConfig(
        type=str(database_raw["type"]),
        host=str(database_raw["host"]),
        port=int(database_raw["port"]),
        database=str(database_raw["database"]),
        user=str(database_raw["user"]),
        password=str(database_raw.get("password", "")),
    )
    workload = WorkloadConfig(
        duration_seconds=int(workload_raw.get("duration_seconds", 60)),
        virtual_users=int(workload_raw.get("virtual_users", 1)),
        think_time_ms=int(workload_raw.get("think_time_ms", 250)),
    )
    scenario = ScenarioConfig(
        name=str(scenario_raw["name"]),
        options=dict(scenario_raw.get("options", {})),
    )
    return AppConfig(
        database=database,
        workload=workload,
        scenario=scenario,
    )

# Made with Bob

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DatabaseConfig:
    type: str
    host: str
    port: int
    database: str
    user: str
    password: str = ""


@dataclass(slots=True)
class WorkloadConfig:
    duration_seconds: int = 60
    virtual_users: int = 1
    think_time_ms: int = 250


@dataclass(slots=True)
class ScenarioConfig:
    name: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppConfig:
    database: DatabaseConfig
    workload: WorkloadConfig
    scenario: ScenarioConfig


@dataclass(slots=True)
class OperationDefinition:
    name: str
    weight: int


@dataclass(slots=True)
class ExecutionPlan:
    operations: list[OperationDefinition]

# Made with Bob

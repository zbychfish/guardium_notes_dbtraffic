from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DatabaseConfig:
    type: str
    host: str
    port: int
    database: str
    user: str
    password: str = ""


@dataclass
class WorkloadConfig:
    duration_seconds: int = 60
    virtual_users: int = 1
    think_time_ms: int = 250


@dataclass
class ScenarioConfig:
    name: str
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    database: DatabaseConfig
    workload: WorkloadConfig
    scenario: ScenarioConfig


@dataclass
class OperationDefinition:
    name: str
    weight: int


@dataclass
class ExecutionPlan:
    operations: List[OperationDefinition]

# Made with Bob

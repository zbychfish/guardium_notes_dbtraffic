from typing import TYPE_CHECKING

from guardium_notes_dbtraffic.models import AppConfig, ExecutionPlan


class Scenario:
    name = "base"

    def build_execution_plan(self, config: AppConfig, duration_seconds: int) -> ExecutionPlan:
        raise NotImplementedError


class ScenarioRegistry:
    def __init__(self) -> None:
        self._scenarios: dict[str, Scenario] = {}

    def register(self, scenario: Scenario) -> None:
        self._scenarios[scenario.name] = scenario

    def get(self, name: str) -> Scenario:
        return self._scenarios[name]

    def list_scenarios(self) -> list[str]:
        return sorted(self._scenarios.keys())


def build_registry() -> ScenarioRegistry:
    from guardium_notes_dbtraffic.scenarios_micro_payments import MicroPaymentsScenario

    registry = ScenarioRegistry()
    registry.register(MicroPaymentsScenario())
    return registry

# Made with Bob

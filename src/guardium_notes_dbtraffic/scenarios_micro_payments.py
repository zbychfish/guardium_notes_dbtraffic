from dataclasses import dataclass
from typing import TYPE_CHECKING

from guardium_notes_dbtraffic.models import ExecutionPlan, OperationDefinition
from guardium_notes_dbtraffic.registry import Scenario

if TYPE_CHECKING:
    from guardium_notes_dbtraffic.models import AppConfig


@dataclass
class MicroPaymentsDefaults:
    customer_lookup_weight: int = 90
    add_customer_weight: int = 4
    add_credit_card_weight: int = 2
    buy_feature_weight: int = 4
    info_types: tuple[str, ...] = (
        "name_surname",
        "email",
        "users_from_city",
        "has_user_cc",
        "extras_per_user",
        "features_per_user",
        "get_addons_per_user",
        "get_extras_per_time",
        "get_user_transactions",
    )


class MicroPaymentsScenario(Scenario):
    name = "micro_payments"

    def build_execution_plan(self, config: "AppConfig", duration_seconds: int) -> ExecutionPlan:
        defaults = MicroPaymentsDefaults()
        operations = [
            OperationDefinition(name="get_customer_info", weight=defaults.customer_lookup_weight),
            OperationDefinition(name="add_customer", weight=defaults.add_customer_weight),
            OperationDefinition(name="add_credit_card", weight=defaults.add_credit_card_weight),
            OperationDefinition(name="buy_feature", weight=defaults.buy_feature_weight),
        ]
        return ExecutionPlan(operations=operations)

    def describe(self, config: "AppConfig") -> dict[str, object]:
        defaults = MicroPaymentsDefaults()
        return {
            "scenario": self.name,
            "database_type": config.database.type,
            "workload_duration_seconds": config.workload.duration_seconds,
            "virtual_users": config.workload.virtual_users,
            "think_time_ms": config.workload.think_time_ms,
            "info_types": list(defaults.info_types),
            "options": config.scenario.options,
        }

# Made with Bob

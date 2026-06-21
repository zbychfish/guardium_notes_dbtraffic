import argparse
from pathlib import Path

from guardium_notes_dbtraffic.config import load_config
from guardium_notes_dbtraffic.db import build_adapter
from guardium_notes_dbtraffic.micro_payments_runtime import run_micro_payments
from guardium_notes_dbtraffic.registry import build_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="guardium-notes-dbtraffic",
        description="Universal application traffic generator",
    )
    parser.add_argument(
        "--config",
        default="config/example.yaml",
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print execution plan without running database operations",
    )
    parser.add_argument(
        "--show-sql",
        action="store_true",
        help="Print SQL statements before execution",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-scenarios", help="List available scenarios")
    subparsers.add_parser("validate-config", help="Validate configuration file")
    subparsers.add_parser("deploy-schema", help="Deploy scenario schema objects (requires admin user)")
    subparsers.add_parser("seed-data", help="Seed scenario business data (requires admin user)")
    subparsers.add_parser("cleanup-schema", help="Cleanup scenario schema objects (requires admin user)")
    subparsers.add_parser("rebuild", help="Cleanup, deploy and seed in one command (requires admin user)")
    run_parser = subparsers.add_parser("run", help="Run configured scenario")
    run_parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Duration in minutes (overrides config)",
    )
    run_parser.add_argument(
        "--speed",
        type=str,
        choices=["slow", "normal", "fast", "insane"],
        default=None,
        help="Execution speed: slow=1000ms, normal=250ms, fast=100ms, insane=0ms",
    )
    return parser


def _print_execution_plan(config_path: Path, config, scenario, duration_seconds: int) -> None:
    execution_plan = scenario.build_execution_plan(config, duration_seconds)
    print(f"Configuration valid: {config_path}")
    print(f"Scenario: {scenario.name}")
    print(f"Database type: {config.database.type}")
    print(f"Duration seconds: {duration_seconds}")
    print(f"Operations configured: {len(execution_plan.operations)}")
    for operation in execution_plan.operations:
        print(f"- {operation.name}: weight={operation.weight}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    registry = build_registry()

    if args.command == "list-scenarios":
        for scenario_name in registry.list_scenarios():
            print(scenario_name)
        return

    config_path = Path(args.config)
    config = load_config(config_path)
    scenario = registry.get(config.scenario.name)

    if args.command == "validate-config":
        _print_execution_plan(config_path, config, scenario, config.workload.duration_seconds)
        return

    adapter = build_adapter(config)
    adapter.show_sql = args.show_sql

    if args.command == "deploy-schema":
        adapter.deploy_micro_payments_schema()
        adapter.close()
        print(f"Schema deployed for scenario {scenario.name} on {config.database.type}")
        return

    if args.command == "seed-data":
        adapter.seed_micro_payments_data()
        adapter.close()
        print(f"Seed data inserted for scenario {scenario.name} on {config.database.type}")
        return

    if args.command == "cleanup-schema":
        adapter.cleanup_micro_payments_schema()
        adapter.close()
        print(f"Schema cleaned for scenario {scenario.name} on {config.database.type}")
        return

    if args.command == "rebuild":
        print("Rebuilding schema...")
        adapter.cleanup_micro_payments_schema()
        print("Schema cleaned")
        adapter.deploy_micro_payments_schema()
        print("Schema deployed")
        adapter.seed_micro_payments_data()
        adapter.close()
        print(f"Rebuild complete for scenario {scenario.name} on {config.database.type}")
        return

    if args.command == "run":
        duration_minutes = args.duration if args.duration is not None else (config.workload.duration_seconds // 60)
        duration_seconds = duration_minutes * 60
        
        speed_map = {"slow": 1000, "normal": 250, "fast": 100, "insane": 0}
        think_time_ms = speed_map.get(args.speed, config.workload.think_time_ms) if args.speed else config.workload.think_time_ms
        
        _print_execution_plan(config_path, config, scenario, duration_seconds)
        print(f"Duration: {duration_minutes} minutes ({duration_seconds} seconds)")
        print(f"Think time: {think_time_ms}ms")

        if args.dry_run:
            return

        locale = str(config.scenario.options.get("locale", "pl_PL"))
        stats = run_micro_payments(
            config=config,
            duration_seconds=duration_seconds,
            think_time_ms=think_time_ms,
            locale=locale,
            show_sql=args.show_sql,
        )
        print("Execution completed.")
        print(f"Executed operations: {stats.executed_operations}")
        print(f"get_customer_info: {stats.get_customer_info_count}")
        print(f"add_customer: {stats.add_customer_count}")
        print(f"add_credit_card: {stats.add_credit_card_count}")
        print(f"buy_feature: {stats.buy_feature_count}")

if __name__ == "__main__":
    main()

# Made with Bob

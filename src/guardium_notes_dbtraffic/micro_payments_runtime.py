from __future__ import annotations

from dataclasses import dataclass
from random import choice, randint, random
from time import sleep
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from guardium_notes_dbtraffic.models import AppConfig

from guardium_notes_dbtraffic.db import DatabaseAdapter, build_adapter
from guardium_notes_dbtraffic.micro_payments_data import (
    build_domains,
    generate_citizen_document_id,
    generate_citizen_id,
    generate_date_in_range,
    generate_driver_license,
    generate_mail,
    generate_passport_id,
    generate_phone_number,
)
from guardium_notes_dbtraffic.micro_payments_defaults import APP_INFO_TYPES
from faker import Faker


@dataclass
class RuntimeStats:
    executed_operations: int = 0
    get_customer_info_count: int = 0
    add_customer_count: int = 0
    add_credit_card_count: int = 0
    buy_feature_count: int = 0


def _escape_sql_text(value: str) -> str:
    return value.replace("'", "''")


def _build_customer_insert_sql(database_type: str, locale: str) -> str:
    faker_instance = Faker(locale)
    domains = build_domains(locale)
    sex = choice([0, 1])
    first_name = faker_instance.first_name_male() if sex == 1 else faker_instance.first_name_female()
    last_name = faker_instance.last_name()
    birthday = generate_date_in_range()
    full_name = f"{first_name} {last_name}"
    birthday_sql = (
        f"DATE '{birthday.strftime('%Y-%m-%d')}'"
        if database_type == "oracle"
        else f"'{birthday.strftime('%Y-%m-%d')}'"
    )
    return (
        "INSERT INTO game.customers ("
        "customer_fname, customer_lname, full_name, birthday, citizen_id, birth_place, street, flat_number, "
        "city, zipcode, driving_license, passport_id, citizen_doc_id, mail, phone"
        ") VALUES ("
        f"'{_escape_sql_text(first_name)}', "
        f"'{_escape_sql_text(last_name)}', "
        f"'{_escape_sql_text(full_name)}', "
        f"{birthday_sql}, "
        f"'{_escape_sql_text(generate_citizen_id(locale, birthday, sex, faker_instance))}', "
        f"'{_escape_sql_text(faker_instance.city())}', "
        f"'{_escape_sql_text(faker_instance.street_name())}', "
        f"'{randint(1, 250)}', "
        f"'{_escape_sql_text(faker_instance.city())}', "
        f"'{_escape_sql_text(faker_instance.postcode())}', "
        f"'{_escape_sql_text(generate_driver_license(locale))}', "
        f"'{_escape_sql_text(generate_passport_id(locale))}', "
        f"'{_escape_sql_text(generate_citizen_document_id(locale))}', "
        f"'{_escape_sql_text(generate_mail(first_name, last_name, domains))}', "
        f"'{_escape_sql_text(generate_phone_number(locale, faker_instance))}'"
        ")"
    )


def _customer_id_sql(database_type: str) -> str:
    if database_type == "oracle":
        return "SELECT customer_id FROM game.customers ORDER BY DBMS_RANDOM.VALUE FETCH FIRST 1 ROWS ONLY"
    return "SELECT customer_id FROM game.customers ORDER BY random() LIMIT 1"


def _card_id_sql(database_type: str, customer_id: Any) -> str:
    if database_type == "oracle":
        return f"SELECT card_id FROM game.credit_cards WHERE customer_id = {customer_id} ORDER BY DBMS_RANDOM.VALUE FETCH FIRST 1 ROWS ONLY"
    return f"SELECT card_id FROM game.credit_cards WHERE customer_id = '{customer_id}' ORDER BY random() LIMIT 1"


def _feature_id_sql(database_type: str) -> str:
    if database_type == "oracle":
        return "SELECT feature_id FROM game.features ORDER BY DBMS_RANDOM.VALUE FETCH FIRST 1 ROWS ONLY"
    return "SELECT feature_id FROM game.features ORDER BY random() LIMIT 1"


def _extra_id_sql(database_type: str) -> str:
    if database_type == "oracle":
        return "SELECT extra_id FROM game.extras ORDER BY DBMS_RANDOM.VALUE FETCH FIRST 1 ROWS ONLY"
    return "SELECT extra_id FROM game.extras ORDER BY random() LIMIT 1"


def _get_customer_info_sql(database_type: str, info_type: str) -> str:
    if info_type == "name_surname":
        return "SELECT customer_fname, customer_lname FROM game.customers"
    if info_type == "email":
        return "SELECT mail FROM game.customers"
    if info_type == "users_from_city":
        return "SELECT city, COUNT(*) FROM game.customers GROUP BY city"
    if info_type == "has_user_cc":
        return (
            "SELECT c.full_name, COUNT(cc.card_id) "
            "FROM game.customers c LEFT JOIN game.credit_cards cc ON c.customer_id = cc.customer_id "
            "GROUP BY c.full_name"
        )
    if info_type == "extras_per_user":
        return (
            "SELECT c.full_name, COUNT(t.extra_id) "
            "FROM game.customers c LEFT JOIN game.transactions t ON c.customer_id = t.customer_id "
            "GROUP BY c.full_name"
        )
    if info_type == "features_per_user":
        return (
            "SELECT c.full_name, COUNT(t.feature_id) "
            "FROM game.customers c LEFT JOIN game.transactions t ON c.customer_id = t.customer_id "
            "GROUP BY c.full_name"
        )
    if info_type == "get_addons_per_user":
        return (
            "SELECT c.full_name, COUNT(t.feature_id) + COUNT(t.extra_id) "
            "FROM game.customers c LEFT JOIN game.transactions t ON c.customer_id = t.customer_id "
            "GROUP BY c.full_name"
        )
    if info_type == "get_extras_per_time":
        if database_type == "oracle":
            return (
                "SELECT TO_CHAR(transaction_time, 'YYYY-MM-DD HH24'), COUNT(extra_id) "
                "FROM game.transactions GROUP BY TO_CHAR(transaction_time, 'YYYY-MM-DD HH24')"
            )
        return (
            "SELECT TO_CHAR(transaction_time, 'YYYY-MM-DD HH24'), COUNT(extra_id) "
            "FROM game.transactions GROUP BY TO_CHAR(transaction_time, 'YYYY-MM-DD HH24')"
        )
    return (
        "SELECT c.full_name, COUNT(t.trans_id) "
        "FROM game.customers c LEFT JOIN game.transactions t ON c.customer_id = t.customer_id "
        "GROUP BY c.full_name"
    )


def _build_credit_card_insert_sql(database_type: str, customer_id: Any) -> str:
    card_number = "".join(str(randint(0, 9)) for _ in range(16))
    card_validity = f"{randint(1, 12):02d}/{randint(26, 35)}"
    if database_type == "oracle":
        return (
            "INSERT INTO game.credit_cards (card_number, card_validity, customer_id) VALUES ("
            f"'{card_number}', '{card_validity}', {customer_id})"
        )
    return (
        "INSERT INTO game.credit_cards (customer_id, card_number, card_validity) VALUES ("
        f"'{customer_id}', '{card_number}', '{card_validity}')"
    )


def _build_transaction_insert_sql(database_type: str, customer_id: Any, card_id: Any, feature_id: Any, extra_id: Any) -> str:
    price = randint(1, 15)
    if database_type == "oracle":
        return (
            "INSERT INTO game.transactions (feature_id, extra_id, price, customer_id, card_id) VALUES ("
            f"{feature_id}, {extra_id}, {price}, {customer_id}, {card_id})"
        )
    return (
        "INSERT INTO game.transactions (feature_id, extra_id, price, customer_id, card_id) VALUES ("
        f"'{feature_id}', '{extra_id}', {price}, '{customer_id}', '{card_id}')"
    )


def run_micro_payments(config: AppConfig, duration_seconds: int, think_time_ms: int, locale: str, show_sql: bool = False) -> RuntimeStats:
    stats = RuntimeStats()
    operations = [
        ("get_customer_info", 0.90),
        ("add_customer", 0.04),
        ("add_credit_card", 0.02),
        ("buy_feature", 0.04),
    ]
    info_types = list(APP_INFO_TYPES)
    iterations = max(1, int((duration_seconds * 1000) / max(think_time_ms, 1)))
    
    app_users = config.scenario.options.get("app_users", ["appuser1", "appuser2"])
    app_users = [str(u) for u in app_users]
    default_password = str(config.scenario.options.get("default_password", config.database.password or "Guardium123!"))
    
    session_steps = randint(5, 15)
    current_step = 0
    adapter: DatabaseAdapter | None = None

    for iteration in range(iterations):
        if current_step == 0:
            if adapter is not None:
                adapter.close()
            current_user = choice(app_users)
            session_steps = randint(5, 15)
            user_config = AppConfig(
                database=type(config.database)(
                    type=config.database.type,
                    host=config.database.host,
                    port=config.database.port,
                    database=config.database.database,
                    user=current_user,
                    password=default_password,
                ),
                workload=config.workload,
                scenario=config.scenario,
            )
            adapter = build_adapter(user_config)
            adapter.show_sql = show_sql
            if show_sql:
                print(f"\n[SESSION] Switching to user: {current_user} for {session_steps} operations")
        
        if adapter is None:
            continue
        
        roll = random()
        cumulative = 0.0
        selected_operation = "get_customer_info"
        for operation_name, weight in operations:
            cumulative += weight
            if roll <= cumulative:
                selected_operation = operation_name
                break

        if selected_operation == "get_customer_info":
            info_type = choice(info_types)
            adapter.execute(_get_customer_info_sql(adapter.config.database.type, info_type))
            stats.get_customer_info_count += 1

        elif selected_operation == "add_customer":
            adapter.execute(_build_customer_insert_sql(adapter.config.database.type, locale))
            stats.add_customer_count += 1

        elif selected_operation == "add_credit_card":
            customer_id = adapter.execute_scalar(_customer_id_sql(adapter.config.database.type))
            if customer_id is not None:
                adapter.execute(_build_credit_card_insert_sql(adapter.config.database.type, customer_id))
                stats.add_credit_card_count += 1

        elif selected_operation == "buy_feature":
            customer_id = adapter.execute_scalar(_customer_id_sql(adapter.config.database.type))
            if customer_id is not None:
                card_id = adapter.execute_scalar(_card_id_sql(adapter.config.database.type, customer_id))
                feature_id = adapter.execute_scalar(_feature_id_sql(adapter.config.database.type))
                extra_id = adapter.execute_scalar(_extra_id_sql(adapter.config.database.type))
                if card_id is not None and feature_id is not None and extra_id is not None:
                    adapter.execute(
                        _build_transaction_insert_sql(
                            adapter.config.database.type,
                            customer_id,
                            card_id,
                            feature_id,
                            extra_id,
                        )
                    )
                    stats.buy_feature_count += 1

        stats.executed_operations += 1
        current_step += 1
        
        if current_step >= session_steps:
            current_step = 0
        
        sleep(max(think_time_ms, 0) / 1000.0)
    
    if adapter is not None:
        adapter.close()

    return stats

# Made with Bob
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from random import choice, randint
from typing import Any

from faker import Faker

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
from guardium_notes_dbtraffic.micro_payments_schema import oracle_deploy_sql, postgres_deploy_sql


@dataclass
class SeedCustomer:
    customer_fname: str
    customer_lname: str
    full_name: str
    birthday: datetime
    citizen_id: str
    birth_place: str
    street: str
    flat_number: str
    city: str
    zipcode: str
    driving_license: str
    passport_id: str
    citizen_doc_id: str
    mail: str
    phone: str


def build_seed_customers(locale: str, count: int) -> list[SeedCustomer]:
    faker_instance = Faker(locale)
    domains = build_domains(locale)
    customers: list[SeedCustomer] = []

    for _ in range(count):
        sex = choice([0, 1])
        first_name = faker_instance.first_name_male() if sex == 1 else faker_instance.first_name_female()
        last_name = faker_instance.last_name()
        birthday = generate_date_in_range()
        full_name = f"{first_name} {last_name}"
        customers.append(
            SeedCustomer(
                customer_fname=first_name,
                customer_lname=last_name,
                full_name=full_name,
                birthday=birthday,
                citizen_id=generate_citizen_id(locale, birthday, sex, faker_instance),
                birth_place=faker_instance.city(),
                street=faker_instance.street_name(),
                flat_number=str(randint(1, 250)),
                city=faker_instance.city(),
                zipcode=faker_instance.postcode(),
                driving_license=generate_driver_license(locale),
                passport_id=generate_passport_id(locale),
                citizen_doc_id=generate_citizen_document_id(locale),
                mail=generate_mail(first_name, last_name, domains),
                phone=generate_phone_number(locale, faker_instance),
            )
        )

    return customers


def _escape_sql_text(value: str) -> str:
    return value.replace("'", "''")


def postgres_seed_customer_sql(customers: list[SeedCustomer]) -> list[str]:
    statements: list[str] = []
    for customer in customers:
        statements.append(
            "INSERT INTO game.customers ("
            "customer_fname, customer_lname, full_name, birthday, citizen_id, birth_place, street, flat_number, "
            "city, zipcode, driving_license, passport_id, citizen_doc_id, mail, phone"
            ") VALUES ("
            f"'{_escape_sql_text(customer.customer_fname)}', "
            f"'{_escape_sql_text(customer.customer_lname)}', "
            f"'{_escape_sql_text(customer.full_name)}', "
            f"'{customer.birthday.strftime('%Y-%m-%d')}', "
            f"'{_escape_sql_text(customer.citizen_id)}', "
            f"'{_escape_sql_text(customer.birth_place)}', "
            f"'{_escape_sql_text(customer.street)}', "
            f"'{_escape_sql_text(customer.flat_number)}', "
            f"'{_escape_sql_text(customer.city)}', "
            f"'{_escape_sql_text(customer.zipcode)}', "
            f"'{_escape_sql_text(customer.driving_license)}', "
            f"'{_escape_sql_text(customer.passport_id)}', "
            f"'{_escape_sql_text(customer.citizen_doc_id)}', "
            f"'{_escape_sql_text(customer.mail)}', "
            f"'{_escape_sql_text(customer.phone)}'"
            ")"
        )
    return statements


def oracle_seed_customer_sql(customers: list[SeedCustomer]) -> list[str]:
    statements: list[str] = []
    for customer in customers:
        statements.append(
            "INSERT INTO game.customers ("
            "customer_fname, customer_lname, full_name, birthday, citizen_id, birth_place, street, flat_number, "
            "city, zipcode, driving_license, passport_id, citizen_doc_id, mail, phone"
            ") VALUES ("
            f"'{_escape_sql_text(customer.customer_fname)}', "
            f"'{_escape_sql_text(customer.customer_lname)}', "
            f"'{_escape_sql_text(customer.full_name)}', "
            f"DATE '{customer.birthday.strftime('%Y-%m-%d')}', "
            f"'{_escape_sql_text(customer.citizen_id)}', "
            f"'{_escape_sql_text(customer.birth_place)}', "
            f"'{_escape_sql_text(customer.street)}', "
            f"'{_escape_sql_text(customer.flat_number)}', "
            f"'{_escape_sql_text(customer.city)}', "
            f"'{_escape_sql_text(customer.zipcode)}', "
            f"'{_escape_sql_text(customer.driving_license)}', "
            f"'{_escape_sql_text(customer.passport_id)}', "
            f"'{_escape_sql_text(customer.citizen_doc_id)}', "
            f"'{_escape_sql_text(customer.mail)}', "
            f"'{_escape_sql_text(customer.phone)}'"
            ")"
        )
    return statements


def build_seed_sql(database_type: str, locale: str, seed_customers: int) -> list[str]:
    customers = build_seed_customers(locale=locale, count=seed_customers)
    if database_type == "postgres":
        return postgres_seed_customer_sql(customers)
    if database_type == "oracle":
        return oracle_seed_customer_sql(customers)
    raise ValueError(f"Unsupported database type for seed SQL: {database_type}")


def build_default_scenario_options() -> dict[str, Any]:
    return {
        "locale": "pl_PL",
        "seed_customers": 100,
        "app_users": ["appuser1", "appuser2"],
        "admin_users": ["adminuser1"],
        "default_password": "Guardium123!",
        "info_types": list(APP_INFO_TYPES),
    }

# Made with Bob
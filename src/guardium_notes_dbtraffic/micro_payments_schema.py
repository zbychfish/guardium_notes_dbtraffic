from guardium_notes_dbtraffic.micro_payments_constants import ADMIN_ROLE_NAME, APP_ROLE_NAME, SCHEMA_NAME
from guardium_notes_dbtraffic.micro_payments_defaults import EXTRA_DESCRIPTIONS, EXTRA_PRICES, FEATURE_DESCRIPTIONS, FEATURE_PRICES


def postgres_cleanup_sql(app_users: list[str], admin_users: list[str]) -> list[str]:
    statements: list[str] = []
    for user in app_users:
        statements.append(
            f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolcanlogin = true AND rolname = '{user}') "
            f"THEN EXECUTE 'DROP USER {user}'; END IF; END $$;"
        )
    for user in admin_users:
        statements.append(
            f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolcanlogin = true AND rolname = '{user}') "
            f"THEN EXECUTE 'DROP USER {user}'; END IF; END $$;"
        )
    statements.extend(
        [
            f"DROP SCHEMA IF EXISTS {SCHEMA_NAME} CASCADE",
            f"DROP ROLE IF EXISTS {ADMIN_ROLE_NAME}",
            f"DROP ROLE IF EXISTS {APP_ROLE_NAME}",
        ]
    )
    return statements


def postgres_deploy_sql(app_users: list[str], admin_users: list[str], default_password: str) -> list[str]:
    statements = [
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',
        f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}",
        f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ADMIN_ROLE_NAME}') THEN CREATE ROLE {ADMIN_ROLE_NAME}; END IF; END $$;",
        f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE_NAME}') THEN CREATE ROLE {APP_ROLE_NAME}; END IF; END $$;",
    ]
    for user in app_users:
        statements.extend(
            [
                f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolcanlogin = true AND rolname = '{user}') THEN CREATE USER {user} LOGIN PASSWORD '{default_password}'; END IF; END $$;",
                f"GRANT {APP_ROLE_NAME} TO {user}",
            ]
        )
    for user in admin_users:
        statements.extend(
            [
                f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolcanlogin = true AND rolname = '{user}') THEN CREATE USER {user} LOGIN PASSWORD '{default_password}'; END IF; END $$;",
                f"GRANT {ADMIN_ROLE_NAME} TO {user}",
            ]
        )
    statements.extend(
        [
            f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.customers ("
            "customer_id UUID DEFAULT uuid_generate_v4(),"
            "customer_fname varchar(50),"
            "customer_lname varchar(50),"
            "full_name varchar(100),"
            "birthday date,"
            "citizen_id varchar(20),"
            "birth_place varchar(50),"
            "street varchar(50),"
            "flat_number varchar(10),"
            "city varchar(50),"
            "zipcode varchar(10),"
            "driving_license varchar(30),"
            "passport_id varchar(30),"
            "citizen_doc_id varchar(30),"
            "mail varchar(50),"
            "phone varchar(30))",
            f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'customers_pk') THEN ALTER TABLE {SCHEMA_NAME}.customers ALTER COLUMN customer_id SET NOT NULL; ALTER TABLE {SCHEMA_NAME}.customers ADD CONSTRAINT customers_pk PRIMARY KEY (customer_id); END IF; END $$;",
            f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.credit_cards (card_id UUID DEFAULT uuid_generate_v4(), customer_id UUID REFERENCES {SCHEMA_NAME}.customers (customer_id), card_number varchar(30), card_validity varchar(12))",
            f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cc_pk') THEN ALTER TABLE {SCHEMA_NAME}.credit_cards ADD CONSTRAINT cc_pk PRIMARY KEY (card_id); END IF; END $$;",
            f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.features (feature_id UUID DEFAULT uuid_generate_v4(), feature_name varchar(40), feature_price real)",
            f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'features_pk') THEN ALTER TABLE {SCHEMA_NAME}.features ADD CONSTRAINT features_pk PRIMARY KEY (feature_id); END IF; END $$;",
            f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.extras (extra_id UUID DEFAULT uuid_generate_v4(), extra_name varchar(40), extra_price real)",
            f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'extras_pk') THEN ALTER TABLE {SCHEMA_NAME}.extras ADD CONSTRAINT extras_pk PRIMARY KEY (extra_id); END IF; END $$;",
            f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.transactions (trans_id UUID DEFAULT uuid_generate_v4(), feature_id UUID REFERENCES {SCHEMA_NAME}.features (feature_id), extra_id UUID REFERENCES {SCHEMA_NAME}.extras (extra_id), price real, customer_id UUID REFERENCES {SCHEMA_NAME}.customers (customer_id), card_id UUID REFERENCES {SCHEMA_NAME}.credit_cards (card_id), transaction_time TIMESTAMP DEFAULT now())",
        ]
    )
    for feature_name, feature_price in zip(FEATURE_DESCRIPTIONS, FEATURE_PRICES, strict=True):
        escaped_feature_name = feature_name.replace("'", "''")
        statements.append(
            f"INSERT INTO {SCHEMA_NAME}.features (feature_name, feature_price) VALUES ('{escaped_feature_name}', {feature_price})"
        )
    for extra_name, extra_price in zip(EXTRA_DESCRIPTIONS, EXTRA_PRICES, strict=True):
        escaped_extra_name = extra_name.replace("'", "''")
        statements.append(
            f"INSERT INTO {SCHEMA_NAME}.extras (extra_name, extra_price) VALUES ('{escaped_extra_name}', {extra_price})"
        )
    statements.extend(
        [
            f"GRANT USAGE ON SCHEMA {SCHEMA_NAME} TO {APP_ROLE_NAME}",
            f"GRANT USAGE ON SCHEMA {SCHEMA_NAME} TO {ADMIN_ROLE_NAME}",
            f"GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA_NAME} TO {ADMIN_ROLE_NAME}",
            f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA {SCHEMA_NAME} TO {APP_ROLE_NAME}",
        ]
    )
    return statements


def oracle_cleanup_sql(app_users: list[str], admin_users: list[str]) -> list[str]:
    statements: list[str] = []
    for user in app_users + admin_users:
        statements.append(
            "BEGIN EXECUTE IMMEDIATE 'DROP USER "
            + user
            + " CASCADE'; EXCEPTION WHEN OTHERS THEN IF SQLCODE != -1918 THEN RAISE; END IF; END;"
        )
    statements.append(
        "BEGIN EXECUTE IMMEDIATE 'DROP USER "
        + SCHEMA_NAME
        + " CASCADE'; EXCEPTION WHEN OTHERS THEN IF SQLCODE != -1918 THEN RAISE; END IF; END;"
    )
    return statements


def oracle_deploy_sql(app_users: list[str], admin_users: list[str], default_password: str) -> list[str]:
    statements = [
        f"CREATE USER {SCHEMA_NAME} IDENTIFIED BY accountwillbelocked",
        f"ALTER USER {SCHEMA_NAME} QUOTA UNLIMITED ON USERS",
    ]
    for user in app_users:
        statements.extend(
            [
                f"CREATE USER {user} IDENTIFIED BY \"{default_password}\"",
                f"GRANT CREATE SESSION TO {user}",
            ]
        )
    for user in admin_users:
        statements.extend(
            [
                f"CREATE USER {user} IDENTIFIED BY \"{default_password}\"",
                f"GRANT CREATE SESSION TO {user}",
            ]
        )
    statements.extend(
        [
            f"CREATE TABLE {SCHEMA_NAME}.customers (customer_id NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY, customer_fname varchar(50), customer_lname varchar(50), full_name varchar(100), birthday date, citizen_id varchar(20), birth_place varchar(50), street varchar(50), flat_number varchar(10), city varchar(50), zipcode varchar(10), driving_license varchar(30), passport_id varchar(30), citizen_doc_id varchar(30), mail varchar(50), phone varchar(30))",
            f"CREATE TABLE {SCHEMA_NAME}.credit_cards (card_id NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY, card_number varchar(30), card_validity varchar(12), customer_id NUMBER NOT NULL, CONSTRAINT fk_user FOREIGN KEY (customer_id) REFERENCES {SCHEMA_NAME}.customers(customer_id))",
            f"CREATE TABLE {SCHEMA_NAME}.features (feature_id NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY, feature_name varchar(50), feature_price real)",
            f"CREATE TABLE {SCHEMA_NAME}.extras (extra_id NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY, extra_name varchar(50), extra_price real)",
            f"CREATE TABLE {SCHEMA_NAME}.transactions (trans_id NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY, feature_id NUMBER, extra_id NUMBER, price real, customer_id NUMBER NOT NULL, card_id NUMBER NOT NULL, transaction_time TIMESTAMP DEFAULT SYSDATE NOT NULL, CONSTRAINT fk_feature FOREIGN KEY (feature_id) REFERENCES {SCHEMA_NAME}.features(feature_id), CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES {SCHEMA_NAME}.customers(customer_id), CONSTRAINT fk_card FOREIGN KEY (card_id) REFERENCES {SCHEMA_NAME}.credit_cards(card_id), CONSTRAINT fk_extra FOREIGN KEY (extra_id) REFERENCES {SCHEMA_NAME}.extras(extra_id))",
        ]
    )
    for feature_name, feature_price in zip(FEATURE_DESCRIPTIONS, FEATURE_PRICES, strict=True):
        escaped_feature_name = feature_name.replace("'", "''")
        statements.append(
            f"INSERT INTO {SCHEMA_NAME}.features (feature_name, feature_price) VALUES ('{escaped_feature_name}', {feature_price})"
        )
    for extra_name, extra_price in zip(EXTRA_DESCRIPTIONS, EXTRA_PRICES, strict=True):
        escaped_extra_name = extra_name.replace("'", "''")
        statements.append(
            f"INSERT INTO {SCHEMA_NAME}.extras (extra_name, extra_price) VALUES ('{escaped_extra_name}', {extra_price})"
        )
    for user in app_users:
        for table_name in ["customers", "credit_cards", "features", "transactions", "extras"]:
            statements.append(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {SCHEMA_NAME}.{table_name} TO {user}")
    for user in admin_users:
        statements.append(f"GRANT DBA TO {user}")
    return statements

# Made with Bob

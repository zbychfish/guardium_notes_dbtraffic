from __future__ import annotations

from datetime import datetime, timedelta
from random import choice, randint
import string

from faker import Faker

from guardium_notes_dbtraffic.micro_payments_defaults import GLOBAL_DOMAINS, POLISH_DOMAINS


def build_domains(locale: str) -> list[str]:
    domains = list(GLOBAL_DOMAINS)
    if locale == "pl_PL":
        domains.extend(POLISH_DOMAINS)
    return domains


def generate_date_in_range(start_year: int = 1950, end_year: int = 2005) -> datetime:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(seconds=randint(0, int((end - start).total_seconds())))


def leading_zeros(value: str, length: int) -> str:
    value = ("0000000000" + str(value))
    return value[len(value) - length:]


def generate_citizen_id(locale: str, date: datetime, sex: int, faker_instance: Faker) -> str:
    if locale == "pl_PL":
        if date.year < 1999:
            pesel = date.strftime("%y%m%d")
        else:
            pesel = date.strftime("%y%m%d")[:2] + str(int(date.strftime("%m")) + 20).zfill(2) + date.strftime("%d")
        pesel += "".join(choice(string.digits) for _ in range(3))
        pesel += choice(["0", "2", "4", "6", "8"] if sex == 0 else ["1", "3", "5", "7", "9"])
        checksum = 0
        for index, factor in enumerate([1, 3, 7, 9, 1, 3, 7, 9, 1, 3]):
            checksum += int(pesel[index]) * factor
        control = 10 - checksum % 10 if checksum % 10 != 0 else 0
        return pesel + str(control)
    if locale == "en_US":
        return faker_instance.ssn()
    return ""


def generate_driver_license(locale: str) -> str:
    if locale != "pl_PL":
        return ""
    counties_codes = [[2, 26], [4, 19], [6, 20], [8, 12], [10, 21], [12, 19], [14, 38], [16, 11], [18, 21],
                      [20, 14], [22, 16], [24, 17], [26, 13], [28, 19], [30, 31], [32, 18]]
    cities_codes = [[2, 65], [4, 64], [6, 64], [8, 62], [10, 63], [12, 63], [14, 65], [16, 61], [18, 64], [20, 63],
                    [22, 64], [24, 78], [26, 61], [28, 62], [30, 64], [32, 63]]
    license_id = leading_zeros(str(randint(1, 99999)), 5)
    license_id += "/"
    license_id += leading_zeros(str(randint(2, int(str(datetime.now().year)[2:]))), 2) + "/"
    if choice([0, 1]):
        county = choice(counties_codes)
        license_id += leading_zeros(str(county[0]), 2)
        license_id += leading_zeros(str(randint(1, county[1])), 2)
    else:
        county = choice(cities_codes)
        license_id += leading_zeros(str(county[0]), 2)
        license_id += leading_zeros(str(randint(61, county[1])), 2)
    return license_id


def generate_passport_id(locale: str) -> str:
    if locale != "pl_PL":
        return ""
    weights = [7, 3, 9, 7, 3, 1, 7, 3]
    symbols = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "R", "S", "T", "U", "V",
               "W", "X", "Y", "Z"]
    values: list[int] = []
    passport = ""
    for _ in range(2):
        symbol = choice(symbols)
        passport += symbol
        values.append(ord(symbol) - 55)
    digits = leading_zeros(str(randint(0, 999999)), 6)
    for digit in digits:
        values.append(int(digit))
    checksum = 0
    for index in range(8):
        checksum += values[index] * weights[index]
    passport += digits[:1]
    passport += str(10 - checksum % 10) if checksum % 10 != 0 else "0"
    return passport + digits[1:]


def generate_citizen_document_id(locale: str) -> str:
    if not locale:
        return ""
    weights = [7, 3, 1, 7, 3, 1, 7, 3]
    symbols = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "P", "R", "S", "T", "U", "V",
               "W", "X", "Y", "Z"]
    values: list[int] = []
    document_id = ""
    for _ in range(3):
        symbol = choice(symbols)
        document_id += symbol
        values.append(ord(symbol) - 55)
    digits = leading_zeros(str(randint(0, 99999)), 5)
    for digit in digits:
        values.append(int(digit))
    checksum = 0
    for index in range(8):
        checksum += values[index] * weights[index]
    return document_id + str(checksum % 10) + digits


def remove_accents(input_text: str) -> str:
    replacements = {
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ś": "s", "ż": "z", "ź": "z",
        "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N", "Ó": "O", "Ś": "S", "Ż": "Z", "Ź": "Z",
    }
    return "".join(replacements.get(char, char) for char in input_text)


def generate_mail(first_name: str, last_name: str, domains: list[str]) -> str:
    first_name = remove_accents(first_name.lower())
    last_name = remove_accents(last_name.lower())
    if choice([True, False]):
        prefix = f"{first_name}.{last_name}"
    elif choice([True, False]):
        prefix = f"{first_name[:1]}{last_name}"
    else:
        prefix = f"{first_name[:1]}.{last_name}"
    return f"{prefix}@{choice(domains)}"


def generate_phone_number(locale: str, faker_instance: Faker) -> str:
    if locale != "pl_PL":
        return faker_instance.phone_number()
    prefixes = ["45", "50", "51", "53", "57", "60", "66", "69", "72", "73", "78", "79", "88"]
    phone = choice(prefixes) + leading_zeros(str(randint(0, 9999999)), 7)
    if choice([True, False]):
        phone = phone[:3] + "-" + phone[3:6] + "-" + phone[6:9]
    return phone if choice([True, False]) else "+48" + phone

# Made with Bob

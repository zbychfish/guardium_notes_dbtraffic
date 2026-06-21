# Quick Start Guide

## Instalacja

### 1. Utwórz i aktywuj środowisko wirtualne

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 2. Zainstaluj pakiet w trybie edytowalnym

**WAŻNE:** Pakiet MUSI być zainstalowany, aby polecenie `guardium-notes-dbtraffic` było dostępne!

```bash
pip install -e .
```

Alternatywnie, możesz uruchomić bezpośrednio przez Python (bez instalacji):

```bash
python -m guardium_notes_dbtraffic.cli --help
```

Lub:

```bash
python src/guardium_notes_dbtraffic/cli.py --help
```

## Użycie

### Wyświetl pomoc

```bash
guardium-notes-dbtraffic --help
```

Lub bezpośrednio przez Python:

```bash
python -m guardium_notes_dbtraffic.cli --help
```

### Dostępne komendy

1. **Lista dostępnych scenariuszy:**
```bash
guardium-notes-dbtraffic list-scenarios
```

2. **Walidacja konfiguracji:**
```bash
guardium-notes-dbtraffic --config config/example.yaml validate-config
```

3. **Wdrożenie schematu bazy danych:**
```bash
guardium-notes-dbtraffic --config config/example.yaml deploy-schema
```

4. **Zasilenie danymi testowymi:**
```bash
guardium-notes-dbtraffic --config config/example.yaml seed-data
```

5. **Uruchomienie generatora ruchu:**
```bash
guardium-notes-dbtraffic --config config/example.yaml run
```

6. **Uruchomienie z niestandardowym czasem trwania:**
```bash
guardium-notes-dbtraffic --config config/example.yaml run --duration-seconds 300
```

7. **Tryb dry-run (bez wykonywania operacji):**
```bash
guardium-notes-dbtraffic --config config/example.yaml --dry-run run
```

8. **Czyszczenie schematu:**
```bash
guardium-notes-dbtraffic --config config/example.yaml cleanup-schema
```

## Konfiguracja

Skopiuj i dostosuj przykładowy plik konfiguracyjny:

```bash
cp config/example.yaml config/my-config.yaml
```

Edytuj `config/my-config.yaml` i ustaw:
- Parametry połączenia z bazą danych (host, port, user, password)
- Typ bazy danych (postgres, oracle, mysql, etc.)
- Parametry obciążenia (duration_seconds, virtual_users, think_time_ms)
- Scenariusz do uruchomienia

## Przykładowy workflow

```bash
# 1. Zainstaluj pakiet
pip install -e .

# 2. Sprawdź dostępne scenariusze
guardium-notes-dbtraffic list-scenarios

# 3. Zwaliduj konfigurację
guardium-notes-dbtraffic --config config/example.yaml validate-config

# 4. Wdróż schemat
guardium-notes-dbtraffic --config config/example.yaml deploy-schema

# 5. Załaduj dane testowe
guardium-notes-dbtraffic --config config/example.yaml seed-data

# 6. Uruchom generator ruchu
guardium-notes-dbtraffic --config config/example.yaml run --duration-seconds 60

# 7. Po zakończeniu testów - wyczyść schemat
guardium-notes-dbtraffic --config config/example.yaml cleanup-schema
```

## Wymagania

- Python >= 3.11
- PyYAML >= 6.0
- faker >= 25.0.0
- Odpowiedni driver bazy danych (psycopg2, cx_Oracle, etc.)

## Troubleshooting

### Błąd: ModuleNotFoundError

Upewnij się, że pakiet jest zainstalowany:
```bash
pip install -e .
```

### Błąd połączenia z bazą danych

Sprawdź:
- Czy baza danych jest uruchomiona
- Czy parametry połączenia w config.yaml są poprawne
- Czy zainstalowany jest odpowiedni driver bazy danych
# Instalacja Python 3.11+ na RHEL 9

## Opcja 1: Użyj dnf (NAJŁATWIEJSZE dla RHEL 9)

RHEL 9 ma Python 3.11 dostępny w repozytoriach!

```bash
# Sprawdź dostępne wersje
sudo dnf module list python3

# Zainstaluj Python 3.11 (nie nadpisze systemowego Python 3.9)
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# Sprawdź instalację
python3.11 --version

# Utwórz venv z Python 3.11
cd /opt/guardium_tz_bootcamp_automation/upload/guardium_notes_dbtraffic
python3.11 -m venv venv

# Aktywuj i zainstaluj
source venv/bin/activate
pip install --upgrade pip
pip install -e .

# Uruchom
guardium-notes-dbtraffic --help
```

**UWAGA:** Python systemowy (python3.9) pozostanie nienaruszony!

## Opcja 2: Użyj pyenv (jeśli dnf nie ma Python 3.11)

```bash
# Zainstaluj wymagane zależności
sudo yum groupinstall -y "Development Tools"
sudo yum install -y gcc make patch zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel

# Zainstaluj pyenv
curl https://pyenv.run | bash

# Dodaj do ~/.bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Przeładuj shell
exec $SHELL

# Zainstaluj Python 3.11
pyenv install 3.11.9

# Ustaw jako lokalną wersję dla projektu
cd /opt/guardium_tz_bootcamp_automation/upload/guardium_notes_dbtraffic
pyenv local 3.11.9

# Utwórz venv z Python 3.11
python -m venv venv
source venv/bin/activate

# Zainstaluj projekt
pip install -e .
```

## Opcja 2: Kompilacja ze źródeł

```bash
# Zainstaluj zależności
sudo yum groupinstall -y "Development Tools"
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel

# Pobierz Python 3.11
cd /tmp
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar xzf Python-3.11.9.tgz
cd Python-3.11.9

# Skompiluj i zainstaluj
./configure --enable-optimizations --prefix=/usr/local
make -j $(nproc)
sudo make altinstall

# Sprawdź instalację
python3.11 --version

# Utwórz venv
cd /opt/guardium_tz_bootcamp_automation/upload/guardium_notes_dbtraffic
python3.11 -m venv venv
source venv/bin/activate

# Zainstaluj projekt
pip install -e .
```

## Opcja 3: Użyj Software Collections (SCL)

```bash
# Włącz EPEL i SCL
sudo yum install -y epel-release
sudo yum install -y centos-release-scl

# Zainstaluj Python 3.11 (jeśli dostępny w SCL)
sudo yum install -y rh-python311

# Aktywuj
scl enable rh-python311 bash

# Utwórz venv
cd /opt/guardium_tz_bootcamp_automation/upload/guardium_notes_dbtraffic
python -m venv venv
source venv/bin/activate

# Zainstaluj projekt
pip install -e .
```

## Opcja 4: Użyj Conda/Miniconda

```bash
# Pobierz Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Utwórz środowisko z Python 3.11
conda create -n guardium python=3.11
conda activate guardium

# Przejdź do projektu i zainstaluj
cd /opt/guardium_tz_bootcamp_automation/upload/guardium_notes_dbtraffic
pip install -e .
```

## Weryfikacja

Po instalacji sprawdź wersję:

```bash
python --version
# Powinno pokazać: Python 3.11.x lub wyżej
```

## Uruchomienie projektu

```bash
cd /opt/guardium_tz_bootcamp_automation/upload/guardium_notes_dbtraffic
source venv/bin/activate  # lub: conda activate guardium

# Sprawdź czy działa
guardium-notes-dbtraffic --help

# Uruchom
guardium-notes-dbtraffic --config config/postgres.yaml deploy-schema
```

## Troubleshooting

### Błąd: "No module named '_ctypes'"
```bash
sudo yum install -y libffi-devel
# Przekompiluj Python
```

### Błąd: "No module named '_ssl'"
```bash
sudo yum install -y openssl-devel
# Przekompiluj Python
```

### Błąd: "No module named '_bz2'"
```bash
sudo yum install -y bzip2-devel
# Przekompiluj Python
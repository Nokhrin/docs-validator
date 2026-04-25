# Разработка

## Создание окружения

```shell
# Клонировать репозиторий
git clone https://github.com/Nokhrin/docs-validator.git
cd docs-validator

# Создать и активировать venv
python3.13 -m venv .venv
source .venv/bin/activate

# Установить проект + dev-зависимости
pip install -e ".[dev]"

# Запустить тесты
pytest
```

---

## Разработка

### 0. Внесение изменений

### 1. Проверка в окружении
pytest tests/unit/ -v

### 2. Проверка в Docker - локальная эмуляция CI
cd .github/local
docker compose up

### 3. Коммит и пуш
git add . && git commit -m "feat: ..." && git push

### 4. Проверка в CI - GitHub Actions - автоматически

---

## Настройка pytest в PyCharm

### Конфигурация/шаблон pytest

```text
# Additional arguments:
-vv --tb=short --color=yes --cov=src/validator --cov-report=term -p no:warnings

# Working directory:
$ProjectFileDir$

# Environment variables:
PYTEST_ADDOPTS="-vv --tb=short --color=yes"
```


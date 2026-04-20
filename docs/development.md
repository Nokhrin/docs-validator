## Быстрый старт

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

## Настройка PyCharm

### Формат вывода pytest

Конфигурация/шаблон pytest
```text
# Additional arguments:
-vv --tb=short --color=yes --cov=src/validator --cov-report=term -p no:warnings

# Working directory:
$ProjectFileDir$

# Environment variables:
PYTEST_ADDOPTS="-vv --tb=short --color=yes"
```
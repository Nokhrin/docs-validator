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

## Процедура тестирования: Пример проекта `notes_and_thoughts`

Данный раздел описывает шаги для проверки работоспособности валидатора на реальном проекте с документацией (`notes_and_thoughts`).

### Шаг 1: Подготовка окружения
### Установка из GitHub

```shell
# 1. Клонировать репозиторий
git clone https://github.com/Nokhrin/docs-validator.git
cd docs-validator

# 2. Создать и активировать виртуальное окружение
python3.13 -m venv .venv
source .venv/bin/activate

# 3. Установить проект и зависимости
pip install -e ".[dev]"
```

После установки команда `docs-validator` станет доступна в терминале.

```shell
docs-validator --help
```

### Шаг 2: Клонирование тестового репозитория
Склонируйте проект с документацией в соседнюю директорию.

```shell
cd ..
git clone https://gitlab.com/Nokhrin/notes_and_thoughts.git
cd docs-validator
```

### Шаг 3: Запуск полной валидации с HTML-отчетом
Выполните сканирование с включенными всеми валидаторами (битые ссылки, сироты, якоря, циклы) и сохраните результат в файл.

```shell
docs-validator scan ../notes_and_thoughts \
  --validate \
  --report html \
  --output /tmp/report_notes_and_thoughts.html \
  --log-level info
```

**Ожидаемый результат:**
- В консоли появится сводка найденных проблем (если они есть).
- Файл `/tmp/report_notes_and_thoughts.html` будет создан и содержать детальную информацию.

### Шаг 4: Анализ результатов
Откройте сгенерированный отчет в браузере:

```shell
xdg-open /tmp/report_notes_and_thoughts.html  # Linux
# или
open /tmp/report_notes_and_thoughts.html      # macOS
```

Проверьте наличие секций:
- **Issues Summary**: Агрегированная статистика по типам ошибок.
- **Broken Links**: Список несуществующих файлов.
- **Orphan Files**: Файлы без входящих ссылок.
- **Missing Anchors**: Ссылки на несуществующие разделы.

### Шаг 5: Проверка строгого режима (CI Simulation)
Эмулируйте поведение CI-пайплайна. Если в проекте есть критические ошибки, команда должна завершиться с кодом `1`.

```shell
docs-validator scan ../notes_and_thoughts --validate --fail-on-error
echo "Exit code: $?"
```

- Если `Exit code: 0` — критических ошибок нет.
- Если `Exit code: 1` — найдены ошибки уровня `ERROR`, требующие исправления.

### Шаг 6: Тестирование с конфигурацией
Создайте файл конфигурации в корне тестируемого проекта для проверки автозагрузки настроек.

```shell
cd ../notes_and_thoughts
cat > .docs-validator.toml << 'EOF'
[validator]
path_to_explore = "."
exclude_patterns = [".git", ".venv", "archive"]
is_validate = true
log_level = "warning"
EOF

# Запуск без явных флагов (настройки берутся из файла)
docs-validator scan
```

### Переустановка при отладке
```shell
# В тестируемом проекте/каталоге указать абсолютный или относительный путь к docs-validator
pip install -e ../docs-validator
```

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


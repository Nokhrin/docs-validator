# Documentation Link Validator

Статический анализатор связности документации для репозиториев на базе Markdown. Инструмент обнаруживает битые ссылки, файлы-сироты, отсутствующие якоря и циклические зависимости, генерируя отчеты в форматах Markdown, HTML или JSON для интеграции в CI/CD.

## Применение
### Установка
Установка docs-validator в проекте, требующем проверки связности ссылок

### Требования
- Python 3.13 или выше.

```shell
# 1. Переход в каталог проекта с документацией
cd ~/projects/notes_and_thoughts/

# 2. Создание и активация виртуального окружения
python3.13 -m venv .venv
source .venv/bin/activate

# 3. Установка docs-validator напрямую из GitHub
pip install git+https://github.com/Nokhrin/docs-validator.git

# Проверка установки
docs-validator --help
```
После установки команда `docs-validator` станет доступна в терминале.

---
## Сценарии использования

### 1. Базовое сканирование
Быстрая проверка целостности ссылок без генерации файла отчета.

```shell
docs-validator scan ./docs
```

### 2. Генерация отчета в Markdown
```shell
docs-validator scan ./docs \
  --report markdown \
  --output /tmp/report.md
```

### 3. Генерация интерактивного HTML-отчета
```shell
docs-validator scan ./docs \
  --report html \
  --output /tmp/report.html
```

### 4. Интеграция в CI/CD (строгий режим)
```shell
docs-validator scan ./docs \
  --validate \
  --fail-on-error
```

### 5. Использование конфигурационного файла
Файл `.docs-validator.toml`:
```shell
cat > .docs-validator.toml << 'EOF'
[validator]
path_to_explore = './docs'
exclude_patterns = ['.git', 'node_modules', '*.tmp']
log_level = 'warning'
report_format = 'markdown'
is_validate = true
is_fail_on_error = true
external_timeout_sec = 10
max_threads_number = 5
hosts_to_ignore = ['localhost', '127.0.0.1']
is_skip_external = false
EOF
```

Запуск:
```shell
docs-validator scan
```

### 6. Пропуск проверки внешних ссылок
```shell
docs-validator scan ./docs --skip-external
```

---


## Разработка

### Установка в режиме editable

Для отладки и внесения изменений в код валидатора:

```shell
# 1. Перейдите в каталог целевого проекта
cd ~/projects/notes_and_thoughts

# 2. Активируйте виртуальное окружение проекта
source .venv/bin/activate

# 3. Установите docs-validator в режиме editable из соседней директории
pip install -e ../docs-validator[dev]
```

> Флаг `-e` создает символические ссылки на `src/validator`. Изменения кода применяются мгновенно без переустановки.

### Запуск валидации

```shell
docs-validator scan . --validate --log-level debug
```

### Локальная валидация (pre-commit hook)
Репозиторий использует нативный hook для проверки перед коммитом.
Хук блокирует коммит при ошибке тестов или покрытии <70%

```shell
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```
Проверка без создания коммита
```shell
bash .githooks/pre-commit
```

Пропуск проверки: `git commit --no-verify`


### Итерация разработки

1. Вносите правки в `../docs-validator/src/validator/`.
2. Повторно выполняйте команду валидации. Перекомпиляция или `pip install` не требуются.

### Запуск тестов

```shell
# С покрытием
pytest --cov=src/validator --cov-report=term

# Детальный вывод
pytest tests/unit/ -vv --tb=short
```

### Обновление зависимостей

#### В корне `docs-validator`:

```shell
source .venv/bin/activate
pip install -e ".[dev]"
```

#### В тестируемом проекте:

```shell
cd ../notes_and_thoughts && source .venv/bin/activate
pip install -e ../docs-validator --upgrade
```

---

## Отладка в PyCharm

### Предусловия

- Проект `docs-validator` и тестируемый проект (например, `notes_and_thoughts`) клонированы в соседние директории.
- В тестируемом проекте установлено виртуальное окружение с `docs-validator` в режиме editable.

### Конфигурация запуска для отладки

1. Создайте новую конфигурацию:
   - `Run` -> `Edit Configurations...` -> `+` -> `Python`

2. Заполните параметры:

| Параметр              | Значение                                                  |
|-----------------------|-----------------------------------------------------------|
| Script path           | `path/to/docs-validator/src/validator/cli.py`             |
| Module name           | *(оставьте пустым)*                                       |
| Parameters            | `scan ../notes_and_thoughts --validate --log-level debug` |
| Python interpreter    | Интерпретатор из `.venv` тестируемого проекта             |
| Working directory     | `path/to/notes_and_thoughts`                              |
| Environment variables | `PYTHONDONTWRITEBYTECODE=1;PYTHONUNBUFFERED=1`            |

3. Точки останова:
   - Установите брейкпоинты в `src/validator/validators/`, `src/validator/core/link_extractor.py` или других модулях.

4. Запуск:
   - Нажмите `Debug` (Shift+F9).

### Конфигурация для запуска тестов

1. Создайте конфигурацию:
   - `Run` -> `Edit Configurations...` -> `+` -> `pytest`

2. Параметры:

| Параметр              | Значение                                              |
|-----------------------|-------------------------------------------------------|
| Name                  | `pytest unit tests`                                   |
| Target                | `path/to/docs-validator/tests/unit/`                  |
| Additional arguments  | `-vv --tb=short --color=yes -s --log-cli-level=DEBUG` |
| Working directory     | `$ProjectFileDir$`                                    |
| Environment variables | *(оставьте пустым)*                                   |


---

### Технические нюансы и потенциальные ошибки

| Сценарий                                                          | Причина                                                          | Решение                                                                                                      |
|-------------------------------------------------------------------|------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `docs-validator: command not found`                               | venv не активирован или `PATH` не обновлен                       | Выполните `source .venv/bin/activate` или запустите `python -m validator.cli scan .`                         |
| Читаются настройки из `docs-validator`, а не `notes_and_thoughts` | В `cli.py` конфиг ищется в `Path.cwd() / ".docs-validator.toml"` | Запускайте команду из `notes_and_thoughts` или явно указывайте `--config ./docs-validator.toml`              |
| В отчетах отображаются абсолютные пути                            | `FilesExplorer` строит пути относительно `root_path`             | Передавайте в `scan` относительный путь (`.` или `./docs`), а не абсолютный                                  |
| Зависимости не резолвятся                                         | `pyproject.toml` в `docs-validator` требует `networkx`           | Флаг `[dev]` в `pip install` автоматически установит зависимости из `dependencies` и `optional-dependencies` |


---

## Архитектура и возможности

Инструмент реализует следующие ключевые функции:
1.  Сканирование файлов: Рекурсивный обход каталогов, поддержка `.md` и `.markdown`.
2.  Построение графа связности: Анализ внутренних ссылок для выявления структуры документации.
3.  Валидация:
    *   `BrokenLinkValidator`: Проверка существования целевых файлов.
    *   `OrphanFileValidator`: Поиск изолированных страниц.
    *   `AnchorLinkValidator`: Проверка корректности якорей разделов.
    *   `CircularDependencyValidator`: Обнаружение циклических зависимостей.
4.  Отчетность: Генерация отчетов в форматах Markdown, HTML, JSON.
5.  Конфигурация: Поддержка файла `.docs-validator.toml` с гибкими настройками исключений и поведения.

[Подробнее об архитектуре](docs/architecture.md) | [Спецификация](docs/specification.md) | [Руководство разработчика](docs/development.md)

---

[![Unit Tests](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml/badge.svg)](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml)
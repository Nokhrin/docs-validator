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
Быстрая проверка целостности ссылок без генерации файла отчета (вывод в консоль).

```shell
docs-validator scan ./docs
```

### 2. Генерация отчета в Markdown
Создание текстового отчета с таблицами для публикации в репозитории или просмотра в редакторе.

```shell
docs-validator scan ./docs \
  --report markdown \
  --output /tmp/report.md
```

### 3. Генерация интерактивного HTML-отчета
Создание визуального отчета

```shell
docs-validator scan ./docs \
  --report html \
  --output /tmp/report.html
```

### 4. Интеграция в CI/CD (Строгий режим)
Запуск валидации с возвратом кода ошибки `1` при обнаружении проблем уровня `ERROR`. Используется в пайплайнах сборки для блокировки merge.

```shell
docs-validator scan ./docs \
  --validate \
  --fail-on-error
```

### 5. Использование конфигурационного файла
Автоматическое применение настроек из файла `.docs-validator.toml`, лежащего в корне проекта. Позволяет не передавать флаги вручную.

**Файл `.docs-validator.toml`:**
```shell
cat > .docs-validator.toml << 'EOF'
[validator]
path_to_explore = "./docs"
exclude_patterns = [".git", "node_modules", "*.tmp"]
log_level = "warning"
report_format = "markdown"
is_validate = true
is_fail_on_error = true
EOF
```

**Запуск:**
```shell
# Параметры подтянутся из файла автоматически
docs-validator scan
```

### 6. Исключение специфичных каталогов
Временное исключение директорий через аргументы командной строки (приоритет над конфигом).

```shell
docs-validator scan ./docs --exclude runbook
```

---

## Разработка
### Установка
Установка docs-validator в проекте, требующем проверки связности ссылок

1. Перейдите в каталог целевого проекта:
   ```shell
   cd ~/projects/notes_and_thoughts
   ```
2. Активируйте виртуальное окружение проекта:
   ```shell
   source .venv/bin/activate
   ```
3. Установите `docs-validator` в режиме editable из соседней директории:
   ```shell
   pip install -e ../docs-validator[dev]
   ```
   *Флаг `-e` создает символические ссылки на `src/validator`. Изменения кода применяются мгновенно без переустановки.*
4. Запуск валидации с включенными проверками и детальным логом:
   ```shell
   docs-validator scan . --validate --log-level debug
   ```
5. Итерация разработки:
   - Вносите правки в `../docs-validator/src/validator/`.
   - Повторно выполняйте команду из шага 4. Перекомпиляция или `pip install` не требуются.

### Тесты
Запуск в терминале, с покрытием
```shell
pytest --cov=src/validator --cov-report=term
```

### Обновление зависимостей - повторная установка

#### В корне `docs-validator`
1. Активируйте виртуальное окружение:
```shell
source .venv/bin/activate
```
2. Примените изменения `pyproject.toml`:
```shell
pip install -e ".[dev]"
```

#### В тестируемом проекте (`notes_and_thoughts`)
1. Активируйте окружение тестового проекта:
```shell
cd ../notes_and_thoughts && source .venv/bin/activate
```
2. Обновите ссылку на локальную версию валидатора:
```shell
pip install -e ../docs-validator --upgrade
```


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
1.  **Сканирование файлов**: Рекурсивный обход каталогов, поддержка `.md` и `.markdown`.
2.  **Построение графа связности**: Анализ внутренних ссылок для выявления структуры документации.
3.  **Валидация**:
    *   `BrokenLinkValidator`: Проверка существования целевых файлов.
    *   `OrphanFileValidator`: Поиск изолированных страниц.
    *   `AnchorLinkValidator`: Проверка корректности якорей разделов.
    *   `CircularDependencyValidator`: Обнаружение циклических зависимостей.
4.  **Отчетность**: Генерация отчетов в форматах Markdown, HTML, JSON.
5.  **Конфигурация**: Поддержка файла `.docs-validator.toml` с гибкими настройками исключений и поведения.

[Подробнее об архитектуре](docs/architecture.md) | [Спецификация](docs/specification.md) | [Руководство разработчика](docs/development.md)

---

[![Unit Tests](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml/badge.svg)](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml)
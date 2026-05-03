# Documentation Link Validator

## Зачем вам этот инструмент

Проблема: В больших проектах документация фрагментируется - ссылки ведут на удаленные файлы, якоря устарели после рефакторинга, важные страницы стали «сиротами» без входящих ссылок. Пользователи теряют время, разработчики получают лишние баг-репорты.

Решение: `docs-validator` автоматически проверяет целостность документации перед каждым релизом и находит проблемы до того, как их заметят пользователи.

Результат: Вы получаете отчет в формате Markdown или HTML с полным списком проблем - битые ссылки, файлы-сироты, отсутствующие якоря, циклические зависимости. Отчет можно интегрировать в CI/CD для автоматической блокировки merge при критических ошибках.

---

## Что вы получаете

### Артефакты

| Формат    | Файл          | Как использовать                                               |
|-----------|---------------|----------------------------------------------------------------|
| Markdown  | `report.md`   | Просмотр в любом текстовом редакторе, публикация в репозитории |
| HTML      | `report.html` | Открытие в браузере, навигация по секциям, отправка заказчику  |
| JSON      | `report.json` | Парсинг скриптами, интеграция с внешними системами             |
| CI Status | Exit code     | `0` = успешно, `1` = найдены ошибки уровня ERROR               |

### Пример отчета (Markdown)

```markdown
# Documentation Validator Report

Total files: 42
Total links: 156
Issues found: 3

## Issues

- [ERROR] broken_link: Не найден адресуемый файл: ./missing.md
  - File: README.md:строка 15
- [WARNING] orphan_file: Файл guide/unused.md не содержит входящих ссылок
  - File: guide/unused.md
- [ERROR] missing_anchor: Якорь "#installation" не найден в файле setup.md
  - File: README.md:строка 42

## Files

### README.md
- Title: Главный документ
- Links found: 12

| Type | URI | Anchor | Line |
|--------|-----|--------|-------|
| INTERNAL | ./guide/setup.md | - | 15 |
| INTERNAL | ./api/reference.md | installation | 42 |

```

---

## Быстрый старт

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/Nokhrin/docs-validator.git
cd docs-validator

# Создать и активировать venv
python3.13 -m venv .venv
source .venv/bin/activate

# Установить проект + dev-зависимости
pip install -e ".[dev]"
```

### Проверка документации проекта

```bash
# Базовая проверка с выводом в консоль
docs-validator scan ./docs

# Генерация Markdown-отчета
docs-validator scan ./docs --report markdown --output report.md

# Генерация HTML-отчета с навигацией
docs-validator scan ./docs --report html --output report.html

# Строгий режим: exit code 1 при ошибках ERROR
docs-validator scan ./docs --validate --fail-on-error
```

---

[Архитектура](docs/architecture.md)
[Спецификация](docs/specification.md)
[Разработка](docs/development.md)
[Реализация возможностей](docs/implementation.md)

---

[![Unit Tests](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml/badge.svg)](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml)
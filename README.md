# Documentation Link Validator

Статический анализатор связности документации для репозиториев на базе Markdown. Инструмент обнаруживает битые ссылки, файлы-сироты, отсутствующие якоря и циклические зависимости, генерируя отчеты в форматах Markdown, HTML или JSON для интеграции в CI/CD.

## Установка

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
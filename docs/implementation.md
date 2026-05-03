# Реализация возможностей

## Сканирование файлов
- Поддерживаемые форматы: .md, .markdown
- Рекурсивный обход каталогов
- Исключение по паттернам

## Валидация ссылок
- BrokenLinkValidator: проверка Path.exists()
- OrphanFileValidator: анализ in_degree графа
- AnchorLinkValidator: парсинг заголовков regex

## Отчетность
- MarkdownReporter: таблицы в Markdown
- HTMLReporter: навигация по секциям
- JSON: через serializers.py

---

## Детали

### 1. Обнаружение битых ссылок

Как реализовано: `BrokenLinkValidator` проверяет существование целевых файлов для всех внутренних ссылок.

Команда:
```bash
docs-validator scan ./docs --validate
```

Результат:
```
[ERROR] broken_link: Не найден адресуемый файл: ./missing.md
  - File: README.md:строка 15
```

Действия пользователя:
1. Открыть `report.md` или `report.html`
2. Найти секцию Issues
3. Перейти к указанному файлу и строке
4. Исправить ссылку или создать отсутствующий файл

---

### 2. Обнаружение файлов-сирот

Как реализовано: `OrphanFileValidator` строит граф связности и находит файлы без входящих ссылок (кроме корневых `README.md`, `index.md`).

Команда:
```bash
docs-validator scan ./docs --validate
```

Результат:
```
[WARNING] orphan_file: Файл guide/unused.md не содержит входящих ссылок
  - File: guide/unused.md
```

Действия пользователя:
1. Проверить, нужен ли файл-сирота
2. Если нужен - добавить ссылку из индексного файла
3. Если не нужен - удалить файл

---

### 3. Обнаружение отсутствующих якорей

Как реализовано: `AnchorLinkValidator` извлекает якоря из заголовков Markdown (`# Heading` → `#heading`) и сверяет со ссылками вида `file.md#anchor`.

Команда:
```bash
docs-validator scan ./docs --validate
```

Результат:
```
[ERROR] missing_anchor: Якорь "#installation" не найден в файле setup.md
  - File: README.md:строка 42
```

Действия пользователя:
1. Открыть целевой файл (`setup.md`)
2. Проверить заголовки - якорь генерируется автоматически из текста
3. Исправить ссылку или добавить заголовок с нужным текстом

---

### 4. Генерация отчетов для CI

Как реализовано: `MarkdownReporter` и `HTMLReporter` генерируют отчеты из результатов валидации.

Команда:
```bash
# Markdown для публикации в репозитории
docs-validator scan ./docs --report markdown --output report.md

# HTML для просмотра в браузере
docs-validator scan ./docs --report html --output report.html

# JSON для парсинга скриптами
docs-validator scan ./docs --report json --output report.json
```

Интеграция в CI/CD (`.github/workflows/test.yml`):
```yaml
- name: Validate documentation
  run: |
    docs-validator scan ./docs --validate --fail-on-error --report html --output report.html

- name: Upload report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: documentation-report
    path: report.html
```

---

## Конфигурация

### Файл `.docs-validator.toml`

```toml
[validator]
# Путь к документации
path = "./docs"

# Исключаемые паттерны
exclude = [".git", "node_modules", "*.tmp"]

# Уровень логирования
log_level = "warning"

# Формат отчета по умолчанию
report_format = "markdown"

# Запускать валидацию автоматически
validate = true

# Завершать с ошибкой при ERROR
fail_on_error = true
```

Использование:
```bash
# Использовать настройки из файла
docs-validator scan

# Переопределить настройки из командной строки
docs-validator scan --report html
```
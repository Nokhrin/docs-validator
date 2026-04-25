## Спринт 1: Ядро - сканирование и парсинг ссылок

| Шаг | Задача              | Файл                                   |
|-----|---------------------|----------------------------------------|
| 1.1 | Модель данных       | `src/validator/core/models.py`         |
| 1.2 | Сканирование файлов | `src/validator/core/files_explorer.py` |
| 1.3 | Парсинг ссылок      | `src/validator/core/link_extractor.py` |
| 1.4 | CLI интерфейс       | `src/validator/cli.py`                 |
| 1.5 | Тесты               | `tests/unit/`                          |
| 1.6 | Интеграция          | `pyproject.toml`                       |

## Спринт 2: Ядро - граф зависимостей; Валидаторы

| Шаг | Задача                                      | Файл                                      | Критерий готовности                                        |
|-----|---------------------------------------------|-------------------------------------------|------------------------------------------------------------|
| 2.1 | Граф зависимостей                           | `src/validator/core/graph.py`             | `ConnectivityGraph` строит граф из `FileToValidate[]`      |
| 2.2 | BrokenLinkValidator                         | `src/validator/validators/broken_link.py` | Проверяет `Path.exists()` для внутренних ссылок            |
| 2.3 | OrphanFileValidator                         | `src/validator/validators/orphan_file.py` | Находит файлы с `in_degree == 0` (кроме корневых)          |
| 2.4 | AnchorValidator                             | `src/validator/validators/anchor.py`      | Проверяет существование якорей в целевых файлах            |
| 2.5 | Интеграция в CLI                            | `src/validator/cli.py`                    | `--validate` флаг запускает валидаторы                     |
| 2.6 | Тесты валидаторов                           | `tests/unit/test_validators.py`           | Фикстуры с битыми ссылками, сиротами, недостающими якорями |
| 2.7 | Зависимость networkx (операции над графами) | `pyproject.toml`                          | `networkx>=3.0` в `dependencies`                           |

## Спринт 3: Интеграция валидаторов; Отчётность

| Шаг | Задача                          | Файл                                      | Критерий готовности                     |
|-----|---------------------------------|-------------------------------------------|-----------------------------------------|
| 3.1 | Исправление BrokenLinkValidator | `src/validator/validators/broken_link.py` | Пути разрешаются относительно root_file |
| 3.2 | Исправление OrphanFileValidator | `src/validator/validators/orphan_file.py` | Корректные сообщения об ошибках         |
| 3.3 | Интеграция валидаторов в CLI    | `src/validator/cli.py`                    | --validate запускает валидацию          |
| 3.4 | MarkdownReporter                | `src/validator/reporters/markdown.py`     | Отчёт в Markdown с таблицами            |
| 3.5 | HTMLReporter                    | `src/validator/reporters/html.py`         | HTML-отчёт с навигацией                 |
| 3.6 | Тесты валидаторов               | `tests/unit/test_validators.py`           | 6 тестов, покрытие ≥80%                 |
| 3.7 | Покрытие тестами                | CI workflow                               | --cov-fail-under=70 проходит            |

## Спринт 4: Завершение + Публикация

| Шаг | Задача                      | Файл                                   | Критерий готовности          |
|-----|-----------------------------|----------------------------------------|------------------------------|
| 4.1 | AnchorValidator (полный)    | `src/validator/validators/anchor.py`   | Проверка якорей в файлах     |
| 4.2 | CircularDependencyValidator | `src/validator/validators/circular.py` | Обнаружение циклов           |
| 4.3 | Кэширование                 | `src/validator/utils/cache.py`         | Ускорение повторных запусков |
| 4.4 | Конфигурация через файл     | `src/validator/config.py`              | .docs-validator.toml         |
| 4.5 | Публикация на PyPI          | pyproject.toml                         | v0.1.0 доступен              |
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
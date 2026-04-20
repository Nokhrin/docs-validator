# Documentation Link Validator - WIP

> Статический анализатор связности документации для открытых репозиториев

## Проблема
Документация может фрагментироваться:
- Ссылки ведут на удалённые файлы или несуществующие якоря
- Файлы становятся «сиротами» - на них нет входящих ссылок
- Cross-references устаревают после рефакторинга разделов

Это делает работу с документацией неэффективной для пользователей.

## Решение
`docs-validator` - CLI-инструмент на Python, который:
- Сканирует `.md`/`.html` файлы на наличие внутренних ссылок
- Строит направленный граф связности документации
- Сообщает о битых ссылках, изолированных файлах, отсутствующих якорях
- Генерирует отчёт в Markdown/HTML для интеграции в CI

[Архитектура](docs/architecture.md)
[Спецификация](docs/specification.md)
[Разработка](docs/development.md)

---

[![Unit Tests](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml/badge.svg)](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml)
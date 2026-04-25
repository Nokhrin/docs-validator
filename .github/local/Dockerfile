# Эмуляция GitHub Actions runner (ubuntu-24.04 + Python 3.13)
FROM python:3.13-slim

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY tests/ ./tests/

RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -e ".[dev]"

CMD ["pytest"]
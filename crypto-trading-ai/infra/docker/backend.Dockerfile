FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    sqlalchemy \
    alembic \
    "psycopg[binary]" \
    pydantic \
    pydantic-settings \
    python-dotenv \
    redis \
    httpx \
    pytest \
    ruff

COPY backend /app/backend
COPY shared /app/shared
COPY alembic.ini /app/alembic.ini

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Minimal OS deps (curl used by healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*

# Install deps first (better caching)
COPY requirements.txt /app/requirements.txt
RUN python -m pip install -r /app/requirements.txt

# Copy repo into image
COPY . /app

# Ensure writable dirs exist inside container (also bind-mounted from host)
RUN mkdir -p /app/data /app/logs /app/build

CMD ["python", "-c", "print(\"Use docker-compose to run backend/dashboard\")"]

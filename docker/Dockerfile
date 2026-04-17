FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Minimal OS deps (curl used by healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
  && rm -rf /var/lib/apt/lists/* \
  && addgroup --system cryptbot \
  && adduser --system --ingroup cryptbot --no-create-home --shell /sbin/nologin cryptbot

# Install deps first (better caching)
COPY requirements-pinned.txt /app/requirements-pinned.txt
RUN python -m pip install -r /app/requirements-pinned.txt

# Copy repo into image
COPY . /app

# Ensure writable dirs exist and are owned by the non-root user
RUN mkdir -p /app/data /app/logs /app/build \
  && chown -R cryptbot:cryptbot /app/data /app/logs /app/build


# Health check — verify the Python environment is functional
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import services; print('ok')" || exit 1
# Drop privileges — never run as root in production
USER cryptbot

CMD ["python", "-c", "print(\"Use docker-compose to run backend/dashboard\")"]

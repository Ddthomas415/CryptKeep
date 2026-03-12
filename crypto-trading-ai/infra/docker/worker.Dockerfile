FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir redis sqlalchemy
COPY backend /app/backend
CMD ["python", "-m", "backend.app.workers.events"]

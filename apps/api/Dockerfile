# API Dockerfile (production)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1

# Create non-root user
RUN adduser --disabled-password --gecos "" --uid 10001 app

WORKDIR /app

# Install runtime deps
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy application code
COPY apps/api/aurora /app/aurora
COPY apps/api/prestart.sh /app/prestart.sh
RUN chmod +x /app/prestart.sh

EXPOSE 8000
ENV PORT=8000

USER app

# Run prestart to perform light checks/migrations if desired; then start app
CMD ["bash", "-lc", "/app/prestart.sh && uvicorn aurora.main:app --host 0.0.0.0 --port ${PORT}"]

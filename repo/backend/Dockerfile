FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev build-essential pkg-config curl \
    libmagic1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["sh", "-c", "\
  echo 'Waiting for database...' && \
  for i in $(seq 1 30); do \
    python -c 'import django; django.setup(); from django.db import connection; connection.ensure_connection()' 2>/dev/null && break; \
    echo \"  attempt $i/30...\"; sleep 2; \
  done && \
  python manage.py migrate --noinput && \
  gunicorn medrights.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]

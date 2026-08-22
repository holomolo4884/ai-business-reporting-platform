#!/bin/bash
set -e

# Ждём готовности PostgreSQL
if [ "$DATABASE_HOST" ]; then
    echo "Waiting for PostgreSQL at $DATABASE_HOST:$DATABASE_PORT..."
    while ! python -c "import socket; s = socket.socket(); s.settimeout(2); s.connect(('$DATABASE_HOST', ${DATABASE_PORT:-5432})); s.close()" 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "PostgreSQL is up!"
fi

# Ждём готовности Redis
if [ "$REDIS_HOST" ]; then
    echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
    while ! python -c "import socket; s = socket.socket(); s.settimeout(2); s.connect(('$REDIS_HOST', ${REDIS_PORT:-6379})); s.close()" 2>/dev/null; do
        echo "Redis is unavailable - sleeping"
        sleep 2
    done
    echo "Redis is up!"
fi

# Применяем миграции (только для API сервиса, не для worker/beat)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput
fi

# Собираем статику (только для API сервиса)
if [ "$COLLECT_STATIC" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Выполняем основную команду (gunicorn, celery, и т.д.)
exec "$@"

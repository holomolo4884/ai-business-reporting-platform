# ============================================
# Stage 1: Builder - установка зависимостей
# ============================================
FROM python:3.13-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Системные зависимости для компиляции и WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Создаём виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем Python зависимости
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/prod.txt

# ============================================
# Stage 2: Runtime - финальный образ
# ============================================
FROM python:3.13-slim-bookworm AS runtime

LABEL maintainer="AI Business Reporting Platform" \
      description="Django backend for AI-powered business reporting"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    PATH="/opt/venv/bin:$PATH"

# Runtime зависимости (без build-essential для меньшего размера)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    # WeasyPrint runtime dependencies
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Шрифты для русского языка
    fonts-dejavu \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv

# Создаём рабочую директорию
WORKDIR /app

# Копируем код приложения
COPY . /app/

# Создаём директории для статики и медиа
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appgroup /app

# Копируем entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Переключаемся на непривилегированного пользователя
USER appuser

# Открываем порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Entrypoint для запуска миграций и collectstatic
ENTRYPOINT ["/docker-entrypoint.sh"]

# По умолчанию запускаем gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]

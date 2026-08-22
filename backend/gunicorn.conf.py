import multiprocessing
import os

# Bind address
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# Worker processes
# Рекомендуется: (2 x CPU cores) + 1
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker class
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")

# Timeout (секунды) - увеличен для долгих запросов
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))

# Graceful timeout
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 30))

# Keep-alive
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 5))

# Max requests per worker (перезапуск для избежания утечек памяти)
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 50))

# Logging
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# Process name
proc_name = "ai-business-reporting-api"

# Preload app для экономии памяти
preload_app = os.environ.get("GUNICORN_PRELOAD", "true").lower() == "true"

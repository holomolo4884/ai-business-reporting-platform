# AI Business Reporting Platform — Tasks

## Легенда статусов

- [ ] не начато
- [x] готово

Рекомендуемый порядок:

A → B → C → D → E → F → G → H → I → J → K → L → M → N → O → P → Q → R → S → T → U → V → W → X → Y

Блок Z можно отложить на после MVP.

---

## Текущий фокус

- [ ] Сейчас работаю над: A-01
- [ ] Следующий шаг: A-02

---

# A. Подготовка проекта

- [x] A-01. Выбрать IDE: PyCharm или VS Code
- [x] A-02. Создать репозиторий `ai-business-reporting-platform`
- [x] A-03. Создать структуру проекта: `backend`, `notification-service`, `nginx`, `docs`
- [x] A-04. Настроить `.gitignore`
- [x] A-05. Создать `.env.example`
- [x] A-06. Зафиксировать версию Python 3.12+
- [x] A-07. Создать виртуальное окружение
- [x] A-08. Создать requirements: `base.txt`, `dev.txt`
- [x] A-09. Настроить линтеры: ruff, black, опционально mypy
- [x] A-10. Настроить pre-commit
- [x] A-11. Создать Makefile с командами install, run, test, lint, docker-up

---

# B. Каркас Django

- [x] B-01. Установить Django 5.x
- [x] B-02. Создать Django-проект: `django-admin startproject config .`
- [x] B-03. Создать приложения: accounts, organizations, business_data, metrics, reports, ai, notifications
- [x] B-04. Настроить settings и чтение переменных из `.env`
- [x] B-05. Подключить Django REST Framework
- [x] B-06. Подключить django-filter
- [x] B-07. Подключить drf-spectacular
- [x] B-08. Подключить django-cors-headers
- [x] B-09. Настроить базовые URL: `/api/v1/`
- [x] B-10. Сделать health check endpoint

---

# C. База данных и Redis

- [x] C-01. Поднять PostgreSQL локально или в Docker
- [x] C-02. Поднять Redis локально или в Docker
- [x] C-03. Настроить подключение Django к PostgreSQL
- [x] C-04. Установить psycopg
- [x] C-05. Применить миграции
- [x] C-06. Настроить `REDIS_URL`
- [x] C-07. Проверить подключение к PostgreSQL и Redis

---

# D. Пользователи и JWT

- [x] D-01. Создать кастомную модель User с email
- [x] D-02. Указать `AUTH_USER_MODEL = "accounts.User"`
- [x] D-03. Создать и применить миграции для User
- [x] D-04. Установить и настроить djangorestframework-simplejwt
- [x] D-05. Сделать регистрацию: `POST /api/v1/auth/register/`
- [x] D-06. Сделать получение токенов: `POST /api/v1/auth/token/`
- [x] D-07. Сделать refresh token: `POST /api/v1/auth/token/refresh/`
- [x] D-08. Сделать endpoint текущего пользователя: `GET /api/v1/auth/me/`
- [x] D-09. Проверить хэширование паролей
- [x] D-10. Протестировать auth

---

# E. Организации и участники

- [x] E-01. Создать модель Organization
- [x] E-02. Создать модель OrganizationMember
- [x] E-03. Добавить роли: owner, admin, member
- [x] E-04. Сделать CRUD API для организаций
- [x] E-05. Автоматически назначать создателя организации владельцем
- [x] E-06. Ограничить доступ: пользователь видит только свои организации
- [x] E-07. Сделать API участников организации
- [x] E-08. Проверить права доступа к организациям и участникам

---

# F. Бизнес-данные

- [x] F-01. Создать модель Order
- [x] F-02. Создать модель Expense
- [x] F-03. Привязать Order и Expense к Organization
- [x] F-04. Добавить статусы заказов: pending, paid, cancelled, refunded
- [x] F-05. Добавить индексы по organization_id и датам
- [x] F-06. Создать serializers для Order и Expense
- [x] F-07. Сделать CRUD API для Orders
- [x] F-08. Сделать CRUD API для Expenses
- [x] F-09. Добавить фильтрацию по датам, статусу, категории
- [x] F-10. Добавить пагинацию
- [x] F-11. Ограничить доступ к данным только своими организациями

---

# G. Демо-данные

- [x] G-01. Установить faker и factory-boy
- [x] G-02. Создать management-команду `seed_demo_data`
- [x] G-03. Создать demo user
- [x] G-04. Создать demo organization
- [x] G-05. Сгенерировать demo заказы
- [x] G-06. Сгенерировать demo расходы
- [x] G-07. Распределить данные за последние 30/60/90 дней
- [x] G-08. Проверить работу seed-команды

---

# H. Модель отчётов

- [x] H-01. Создать модель Report
- [x] H-02. Добавить report_type: sales, finance, custom
- [x] H-03. Добавить статусы: pending, collecting_data, calling_ai, completed, failed
- [x] H-04. Добавить period_start и period_end
- [x] H-05. Добавить поле metrics как JSONField
- [x] H-06. Добавить поле ai_response как JSONField
- [x] H-07. Добавить поле generated_text
- [x] H-08. Добавить поле error
- [x] H-09. Добавить поле pdf_file
- [x] H-10. Создать и применить миграции для Report

---

# I. API отчётов

- [x] I-01. Сделать генерацию отчёта: `POST /api/v1/reports/generate/`
- [x] I-02. Добавить валидацию периода
- [x] I-03. Проверять права доступа к организации
- [x] I-04. Возвращать статус созданного отчёта
- [x] I-05. Сделать список отчётов: `GET /api/v1/reports/`
- [x] I-06. Сделать детали отчёта: `GET /api/v1/reports/{id}/`
- [x] I-07. Сделать повторную генерацию: `POST /api/v1/reports/{id}/regenerate/`
- [x] I-08. Сделать скачивание отчёта: `GET /api/v1/reports/{id}/download/`
- [x] I-09. Добавить пагинацию для списка отчётов
- [x] I-10. Добавить фильтрацию отчётов

---

# J. Сервис сбора метрик

- [x] J-01. Создать MetricsService
- [x] J-02. Реализовать sales metrics: revenue, orders_count, average_order_value
- [x] J-03. Реализовать finance metrics: revenue, expenses_total, profit
- [x] J-04. Добавить top categories
- [x] J-05. Опционально добавить сравнение периодов
- [x] J-06. Обработать случай, когда данных нет
- [x] J-07. Проверить корректность работы с датами и таймзонами
- [x] J-08. Написать unit-тесты для MetricsService

---

# K. Celery

- [x] K-01. Установить Celery и Redis
- [x] K-02. Создать `config/celery.py`
- [x] K-03. Настроить Redis как broker
- [x] K-04. Настроить result backend
- [x] K-05. Настроить autodiscover_tasks
- [x] K-06. Проверить простую тестовую Celery-задачу
- [ ] K-07. Настроить `CELERY_TASK_ALWAYS_EAGER` для тестов

---

# L. Фоновая генерация отчёта

- [ ] L-01. Создать Celery-задачу `generate_report_task`
- [ ] L-02. Обновлять статусы Report во время генерации
- [ ] L-03. Вызывать MetricsService внутри задачи
- [ ] L-04. Сохранять собранные metrics в Report
- [ ] L-05. Вызывать AI client внутри задачи
- [ ] L-06. Обрабатывать ошибки и переводить Report в failed
- [ ] L-07. Добавить retry для временных ошибок
- [ ] L-08. Добавить логирование задачи
- [ ] L-09. Протестировать задачу генерации отчёта

---

# M. AI-интеграция

- [ ] M-01. Выбрать AI provider или fake provider
- [ ] M-02. Создать AI client
- [ ] M-03. Добавить timeout для запросов к AI API
- [ ] M-04. Добавить retry для запросов к AI API
- [ ] M-05. Создать prompt template
- [ ] M-06. Требовать от AI ответ в формате JSON
- [ ] M-07. Валидировать ответ AI через Pydantic или schema
- [ ] M-08. Сделать fake AI provider для разработки и тестов
- [ ] M-09. Логировать запросы и ответы AI без секретов
- [ ] M-10. Опционально сохранять токены или стоимость генерации

---

# N. Рендер отчёта

- [ ] N-01. Сделать текстовый рендер отчёта из AI-ответа
- [ ] N-02. Сделать HTML-шаблон отчёта
- [ ] N-03. Добавить генерацию PDF через WeasyPrint или reportlab
- [ ] N-04. Настроить сохранение PDF-файла
- [ ] N-05. Проверить endpoint скачивания отчёта
- [ ] N-06. Проверить корректное отображение кириллицы в PDF

---

# O. Notification-service

- [ ] O-01. Создать папку `notification-service`
- [ ] O-02. Создать FastAPI-приложение
- [ ] O-03. Создать Pydantic-схемы запросов и ответов
- [ ] O-04. Сделать health check: `GET /health/`
- [ ] O-05. Сделать отправку уведомлений: `POST /api/v1/notifications/send/`
- [ ] O-06. Добавить email channel, можно fake
- [ ] O-07. Добавить telegram channel, можно fake
- [ ] O-08. Добавить webhook channel
- [ ] O-09. Логировать уведомления и статусы доставки
- [ ] O-10. Обработать ошибки notification-service

---

# P. Связка Django и notification-service

- [ ] P-01. Создать NotificationClient в Django
- [ ] P-02. Добавить internal API key/token для сервисов
- [ ] P-03. Отправлять уведомление после завершения генерации отчёта
- [ ] P-04. Создать Celery-задачу `send_report_notification_task`
- [ ] P-05. Добавить retry при недоступности notification-service
- [ ] P-06. Сохранять NotificationLog
- [ ] P-07. Протестировать интеграцию с notification-service

---

# Q. Расписания и Celery Beat

- [ ] Q-01. Создать модель ReportSchedule
- [ ] Q-02. Добавить frequency: daily, weekly, monthly
- [ ] Q-03. Сделать CRUD API для ReportSchedule
- [ ] Q-04. Подключить Celery Beat
- [ ] Q-05. Создать периодическую задачу проверки расписаний
- [ ] Q-06. Избежать дублирования отчётов за один период
- [ ] Q-07. Протестировать запуск отчётов по расписанию

---

# R. Swagger и документация

- [ ] R-01. Подключить drf-spectacular
- [ ] R-02. Сделать endpoint `/api/schema/`
- [ ] R-03. Сделать Swagger UI: `/api/docs/`
- [ ] R-04. Улучшить описание request/response схем
- [ ] R-05. Проверить авторизацию в Swagger

---

# S. Права доступа и безопасность

- [ ] S-01. Проверить IsAuthenticated на защищённых endpoint'ах
- [ ] S-02. Сделать permissions для Organization
- [ ] S-03. Сделать object permissions для Order, Expense, Report
- [ ] S-04. Проверить работу ролей owner/admin/member
- [ ] S-05. Убрать секреты из кода и использовать `.env`
- [ ] S-06. Проверить валидацию входных данных
- [ ] S-07. Добавить throttling для login и генерации отчётов

---

# T. Тестирование

- [ ] T-01. Установить pytest, pytest-django, pytest-cov
- [ ] T-02. Настроить pytest в pyproject.toml или pytest.ini
- [ ] T-03. Создать фабрики для User, Organization, Order, Expense
- [ ] T-04. Написать тесты auth
- [ ] T-05. Написать тесты organizations
- [ ] T-06. Написать тесты orders/expenses
- [ ] T-07. Написать тесты MetricsService
- [ ] T-08. Написать тесты reports API
- [ ] T-09. Написать тесты Celery-задач
- [ ] T-10. Написать тесты AI client с fake provider
- [ ] T-11. Написать тесты notification client
- [ ] T-12. Проверить coverage

---

# U. Логирование и наблюдаемость

- [ ] U-01. Настроить базовое логирование Django
- [ ] U-02. Опционально добавить структурированные логи
- [ ] U-03. Логировать Celery-задачи
- [ ] U-04. Логировать вызовы AI API без секретов
- [ ] U-05. Логировать отправку уведомлений
- [ ] U-06. Добавить health checks для Django и FastAPI
- [ ] U-07. Подключить Flower
- [ ] U-08. Опционально подключить Sentry

---

# V. Docker

- [ ] V-01. Создать Dockerfile для backend
- [ ] V-02. Создать Dockerfile для notification-service
- [ ] V-03. Добавить сервис db в docker-compose
- [ ] V-04. Добавить сервис redis в docker-compose
- [ ] V-05. Добавить сервис api в docker-compose
- [ ] V-06. Добавить сервис worker в docker-compose
- [ ] V-07. Добавить сервис beat в docker-compose
- [ ] V-08. Добавить сервис flower в docker-compose
- [ ] V-09. Добавить сервис notification-service в docker-compose
- [ ] V-10. Добавить сервис nginx в docker-compose
- [ ] V-11. Настроить volumes для PostgreSQL и файлов
- [ ] V-12. Проверить сборку и запуск: `docker compose up --build`

---

# W. Nginx

- [ ] W-01. Создать nginx config
- [ ] W-02. Настроить проксирование `/api/` на Django
- [ ] W-03. Настроить проксирование `/notify/` на FastAPI notification-service
- [ ] W-04. Настроить static/media при необходимости
- [ ] W-05. Проверить работу API через Nginx

---

# X. README и презентация проекта

- [ ] X-01. Написать описание проекта
- [ ] X-02. Указать стек технологий
- [ ] X-03. Добавить архитектурную схему
- [ ] X-04. Описать запуск проекта через Docker
- [ ] X-05. Описать переменные окружения
- [ ] X-06. Добавить информацию о seed/demo data
- [ ] X-07. Добавить примеры API-запросов
- [ ] X-08. Добавить примеры API-ответов
- [ ] X-09. Добавить ссылки на Swagger, Flower, health checks
- [ ] X-10. Добавить скриншоты или GIF демо

---

# Y. Финальная проверка MVP

- [ ] Y-01. Проверить регистрацию пользователя
- [ ] Y-02. Проверить JWT login и refresh
- [ ] Y-03. Проверить создание организации
- [ ] Y-04. Проверить CRUD orders и expenses
- [ ] Y-05. Проверить ручную генерацию отчёта
- [ ] Y-06. Проверить работу AI/fake AI provider
- [ ] Y-07. Проверить отправку уведомления
- [ ] Y-08. Проверить работу Celery worker
- [ ] Y-09. Проверить работу Celery Beat
- [ ] Y-10. Проверить Flower
- [ ] Y-11. Проверить, что все тесты проходят
- [ ] Y-12. Проверить запуск через Docker Compose
- [ ] Y-13. Проверить README
- [ ] Y-14. Убрать лишние файлы, секреты и временный код

---

# Z. Дополнительные улучшения после MVP

- [ ] Z-01. Добавить сравнение периодов
- [ ] Z-02. Добавить данные для графиков
- [ ] Z-03. Добавить экспорт в Excel
- [ ] Z-04. Поддержать несколько AI providers
- [ ] Z-05. Добавить feedback на отчёт
- [ ] Z-06. Добавить Events API для приёма внешних событий
- [ ] Z-07. Добавить Redis Streams
- [ ] Z-08. Добавить Prometheus/Grafana
- [ ] Z-09. Подключить Sentry
- [ ] Z-10. Настроить CI/CD

# Telegram Shop Bot + Django Admin

## 📦 Состав проекта
- **Telegram-бот**: каталог, корзина, заказы, оплата
- **Админка Django**: управление товарами, заказами, рассылки, экспорт
- **PostgreSQL**: основная БД
- **Docker**: для сборки и запуска

---

## 🚀 Запуск через Docker

1. Скопируйте `.env` из примера:
   ```bash
   cp .env.example .env
   ```
2. Запустите:
   ```bash
   docker-compose up --build
   ```
3. Откройте админку:
   - [http://localhost:8000/admin](http://localhost:8000/admin)

---

## ⚙️ Переменные окружения (`.env`)
```
POSTGRES_DB=shopdb
POSTGRES_USER=shopuser
POSTGRES_PASSWORD=shoppass
DB_HOST=localhost
DB_PORT=5432

DJANGO_SECRET_KEY=secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*

BOT_TOKEN=ваш_токен_бота
```

---

## 📋 Основные команды
```bash
# Создание миграций
python manage.py makemigrations
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск бота (внутри контейнера bot/)
python main.py
```

---

## 🔐 Функции админки
- ✅ Управление товарами, категориями
- ✅ Просмотр и экспорт заказов в Excel
- ✅ Рассылки по пользователям

---

## 🧰 Зависимости
- Django 4.2+
- Aiogram 3
- asyncpg, SQLAlchemy (если нужно)
- openpyxl (экспорт Excel)
- python-dotenv

---

## 📬 Связь
По вопросам и обратной связи — через Telegram.

---

Сделано с ❤️ для тестового задания

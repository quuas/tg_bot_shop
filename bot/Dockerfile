FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходников
COPY . .

RUN mkdir -p /app/logs && touch /app/logs/backend.log

ENV PYTHONPATH=/app:/app/backend

# Запуск бота
CMD ["python", "main.py"]

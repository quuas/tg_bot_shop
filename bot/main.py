import asyncio
import logging
import os
import django

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Установка конфигурации Django до импорта моделей
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# Импорт хендлеров после настройки Django
from handlers import start, catalog, cart, faq

TOKEN = os.getenv("BOT_TOKEN")
dp = Dispatcher(storage=MemoryStorage())

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="catalog", description="Каталог товаров"),
        BotCommand(command="cart", description="Корзина"),
        BotCommand(command="faq", description="Часто задаваемые вопросы"),
    ]
    await bot.set_my_commands(commands)

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)

    await set_commands(bot)

    # Регистрация всех роутеров
    dp.include_routers(
        start.router,
        catalog.router,
        cart.router,
        faq.router,
    )

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")

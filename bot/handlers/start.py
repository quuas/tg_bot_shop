from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest

router = Router()

CHANNEL_USERNAME = "@its_test_shop"
GROUP_USERNAME = "@for_test_shop"

async def is_user_subscribed(bot: Bot, user_id: int, chat_username: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=chat_username, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest:
        return False

def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url="https://t.me/its_test_shop")],
            [InlineKeyboardButton(text="💬 Вступить в группу", url="https://t.me/for_test_shop")],
            [InlineKeyboardButton(text="🔄 Я подписался", callback_data="retry_start")],
        ]
    )

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    in_channel = await is_user_subscribed(bot, user_id, CHANNEL_USERNAME)
    in_group = await is_user_subscribed(bot, user_id, GROUP_USERNAME)

    if not in_channel or not in_group:
        await message.answer(
            "❗ Для использования бота подпишитесь на канал и группу:",
            reply_markup=get_subscribe_keyboard()
        )
        return

    await message.answer("✅ Добро пожаловать! Вы подписаны на все нужные ресурсы.")

@router.callback_query(F.data == "retry_start")
async def retry_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    in_channel = await is_user_subscribed(bot, user_id, CHANNEL_USERNAME)
    in_group = await is_user_subscribed(bot, user_id, GROUP_USERNAME)

    if in_channel and in_group:
        await callback.message.edit_text("✅ Отлично! Подписка подтверждена.")
    else:
        await callback.answer("⛔ Вы ещё не подписались!", show_alert=True)

from aiogram import Router, types, F
from handlers.start import allowed_users

router = Router()

FAQ_ENTRIES = {
    "доставка": "📦 Мы доставляем товары по всей стране в течение 2–5 рабочих дней.",
    "оплата": "💳 Оплата возможна при получении или онлайн через карту.",
    "возврат": "🔁 Возврат возможен в течение 14 дней с момента получения товара.",
}

@router.message(F.text == "/faq")
async def show_faq(message: types.Message):
    user_id = message.from_user.id

    if user_id not in allowed_users:
        await message.answer("⛔ Пожалуйста, сначала подпишитесь на канал и группу.")
        return
    
    text = "❓ <b>Часто задаваемые вопросы:</b>\n\n"
    for key in FAQ_ENTRIES:
        text += f"• {key.capitalize()}\n"
    text += "\nВведите ключевое слово, чтобы получить ответ."
    await message.answer(text)

@router.message(F.text.lower().in_(FAQ_ENTRIES.keys()))
async def answer_faq(message: types.Message):
    response = FAQ_ENTRIES.get(message.text.lower())
    await message.answer(response)

def register(dp):
    dp.include_router(router)

from aiogram import Router, types, F
from handlers.start import allowed_users
from aiogram.types import InlineQuery
from aiogram.types.inline_query_result_article import InlineQueryResultArticle
from aiogram.types.input_text_message_content import InputTextMessageContent
from uuid import uuid4
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Доставка", switch_inline_query_current_chat="доставка")],
            [InlineKeyboardButton(text="💳 Оплата", switch_inline_query_current_chat="оплата")],
            [InlineKeyboardButton(text="🔁 Возврат", switch_inline_query_current_chat="возврат")]
        ]
    )

    await message.answer(
        "❓ Выберите интересующий вопрос или введите ключевое слово:",
        reply_markup=keyboard
    )

@router.inline_query()
async def inline_faq(query: InlineQuery):
    user_input = query.query.strip().lower()
    results = []

    for keyword, answer in FAQ_ENTRIES.items():
        if keyword in user_input:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=keyword.capitalize(),
                    description=answer[:50],
                    input_message_content=InputTextMessageContent(message_text=answer)
                )
            )

    if not results:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="❌ Ничего не найдено",
                input_message_content=InputTextMessageContent(
                    message_text="По вашему запросу ничего не найдено."
                )
            )
        )

    await query.answer(results, cache_time=1, is_personal=True)

def register(dp):
    dp.include_router(router)

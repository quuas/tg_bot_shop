from aiogram import Router, types, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from store.models import Category, SubCategory, Product

router = Router()

@router.message(F.text == "/catalog")
async def show_categories(callback: CallbackQuery):
    categories = await Category.objects.all().aquery()
    if not categories:
        await callback.message.answer("Каталог пуст.")
        return

    keyboard = [
        [InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")]
        for cat in categories
    ]
    await callback.message.answer("📂 Выберите категорию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("cat_"))
async def show_subcategories(callback: CallbackQuery):
    cat_id = int(callback.data.split("_")[1])
    subcategories = await SubCategory.objects.filter(category_id=cat_id).aquery()
    if not subcategories:
        await callback.message.answer("Нет подкатегорий.")
        return

    keyboard = [
        [InlineKeyboardButton(text=sub.name, callback_data=f"sub_{sub.id}")]
        for sub in subcategories
    ]
    await callback.message.answer("📁 Выберите подкатегорию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("sub_"))
async def show_products(callback: CallbackQuery):
    sub_id = int(callback.data.split("_")[1])
    products = await Product.objects.filter(subcategory_id=sub_id).aquery()
    if not products:
        await callback.message.answer("Нет товаров в этой подкатегории.")
        return

    for product in products:
        text = f"<b>{product.name}</b>\n\n{product.description}\n\n💵 Цена: {product.price} руб."
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_{product.id}")]
            ]
        )
        await callback.message.answer_photo(photo=product.image_url, caption=text, reply_markup=keyboard)

def register(dp):
    dp.include_router(router)

from aiogram import Router, types, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from store.models import Category, SubCategory, Product
from asgiref.sync import sync_to_async
from handlers.start import allowed_users

router = Router()

@router.message(F.text == "/catalog")
async def show_categories(message: Message):
    user_id = message.from_user.id

    if user_id not in allowed_users:
        await message.answer("⛔ Пожалуйста, сначала подпишитесь на канал и группу.")
        return
    
    categories = await sync_to_async(list)(Category.objects.all())
    if not categories:
        await message.answer("Каталог пуст.")
        return

    keyboard = [
        [InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")]
        for cat in categories
    ]
    await message.answer("📂 Выберите категорию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("cat_"))
async def show_subcategories(callback: CallbackQuery):
    cat_id = int(callback.data.split("_")[1])
    subcategories = await sync_to_async(list)(SubCategory.objects.filter(category_id=cat_id))
    if not subcategories:
        await callback.message.answer("Нет подкатегорий.")
        return

    keyboard = [
        [InlineKeyboardButton(text=sub.name, callback_data=f"sub_{sub.id}")]
        for sub in subcategories
    ]
    await callback.message.answer("📁 Выберите подкатегорию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

async def show_product_page(message, products, page, sub_id, category_id):
    total = len(products)
    product = products[page]

    text = (
        f"<b>{product.name}</b>\n\n"
        f"{product.description}\n\n"
        f"💵 Цена: {product.price} руб.\n\n"
        f"<i>Товар {page + 1} из {total}</i>"
    )

    buttons = []

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{sub_id}_{page - 1}"))
    if page < total - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{sub_id}_{page + 1}"))

    buttons.append([InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_{product.id}")])
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"cat_{category_id}")])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await message.edit_media(
            media=types.InputMediaPhoto(media=product.image_url, caption=text),
            reply_markup=reply_markup
        )
    except:
        await message.answer_photo(photo=product.image_url, caption=text, reply_markup=reply_markup)

@router.callback_query(F.data.startswith("sub_"))
async def show_products(callback: CallbackQuery):
    sub_id = int(callback.data.split("_")[1])
    products = await sync_to_async(list)(
        Product.objects.select_related("subcategory").filter(subcategory_id=sub_id)
    )

    if not products:
        await callback.message.answer("Нет товаров в этой подкатегории.")
        return

    category_id = products[0].subcategory.category_id
    await show_product_page(callback.message, products, page=0, sub_id=sub_id, category_id=category_id)

@router.callback_query(F.data.startswith("page_"))
async def paginate_products(callback: CallbackQuery):
    _, sub_id, page = callback.data.split("_")
    sub_id = int(sub_id)
    page = int(page)

    products = await sync_to_async(list)(
        Product.objects.select_related("subcategory").filter(subcategory_id=sub_id)
    )

    category_id = products[0].subcategory.category_id
    await show_product_page(callback.message, products, page, sub_id=sub_id, category_id=category_id)

def register(dp):
    dp.include_router(router)

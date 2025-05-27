from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from store.models import Cart, CartItem, Product, Order, OrderItem
from asgiref.sync import sync_to_async
from handlers.start import allowed_users

router = Router()

class OrderForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()

@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[1])

    cart, _ = await Cart.objects.aget_or_create(user_id=user_id)
    item, created = await CartItem.objects.aget_or_create(cart=cart, product_id=product_id)

    if not created:
        item.quantity += 1
        await item.asave()

    await callback.answer("✅ Товар добавлен в корзину", show_alert=False)

@router.message(F.text == "/cart")
async def show_cart(target: types.Message | types.CallbackQuery):
    user_id = target.from_user.id

    if user_id not in allowed_users:
        await target.answer("⛔ Пожалуйста, сначала подпишитесь на канал и группу.")
        return
    
    try:
        cart = await Cart.objects.aget(user_id=user_id)
        items = await sync_to_async(list)(
            CartItem.objects.select_related("product").filter(cart=cart)
        )
    except Cart.DoesNotExist:
        await target.answer("🛒 Ваша корзина пуста.") if isinstance(target, CallbackQuery) else await target.answer("🛒 Ваша корзина пуста.")
        return

    if not items:
        await target.answer("🛒 Ваша корзина пуста.") if isinstance(target, CallbackQuery) else await target.answer("🛒 Ваша корзина пуста.")
        return

    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    for item in items:
        subtotal = item.quantity * item.product.price
        total += subtotal
        text += f"{item.product.name} — {item.quantity} шт. = {subtotal} руб.\n"

    text += f"\n<b>Итого:</b> {total} руб."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"❌ Удалить {item.product.name}", callback_data=f"remove_{item.product.id}")
        ] for item in items
    ] + [
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="order_start")]
    ])

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=keyboard)
    else:
        await target.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "order_start")
async def order_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderForm.waiting_for_name)
    await callback.message.answer("Введите ваше <b>ФИО</b>:")

@router.message(OrderForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(OrderForm.waiting_for_address)
    await message.answer("Введите <b>адрес доставки</b>:")

@router.message(OrderForm.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    data = await state.get_data()
    full_name = data["full_name"]
    address = message.text
    user_id = message.from_user.id

    cart = await Cart.objects.aget(user_id=user_id)
    items = await sync_to_async(list)(CartItem.objects.select_related("product").filter(cart=cart))
    order = await Order.objects.acreate(
        user_id=user_id,
        full_name=full_name,
        address=address,
        paid=False
    )

    for item in items:
        await OrderItem.objects.acreate(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    await CartItem.objects.filter(cart=cart).adelete()

    await message.answer("🎉 Заказ оформлен! Мы свяжемся с вами для подтверждения.")
    await state.clear()

@router.callback_query(F.data.startswith("remove_"))
async def remove_from_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[1])

    try:
        cart = await Cart.objects.aget(user_id=user_id)
        item = await CartItem.objects.aget(cart=cart, product_id=product_id)
        await item.adelete()
        await callback.answer("🗑️ Товар удалён из корзины", show_alert=False)
    except CartItem.DoesNotExist:
        await callback.answer("❌ Товар не найден в корзине", show_alert=True)

    await show_cart(callback)

def register(dp):
    dp.include_router(router)

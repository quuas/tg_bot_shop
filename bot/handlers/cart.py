from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from store.models import Cart, CartItem, Product, Order, OrderItem
from asgiref.sync import sync_to_async
from handlers.start import allowed_users
from aiogram.types import LabeledPrice
import os
from dotenv import load_dotenv

load_dotenv()
PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

router = Router()

class OrderForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()

class AddToCartForm(StatesGroup):
    waiting_for_quantity = State()

class RemoveFromCartForm(StatesGroup):
    waiting_for_remove_quantity = State()

@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    await state.update_data(product_id=product_id)
    await state.set_state(AddToCartForm.waiting_for_quantity)
    await callback.message.answer("🔢 Укажите количество товара:")

@router.message(AddToCartForm.waiting_for_quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    product_id = data["product_id"]

    try:
        quantity = int(message.text)
        if quantity < 1:
            raise ValueError()
    except ValueError:
        await message.answer("❗ Введите корректное положительное число.")
        return

    cart, _ = await Cart.objects.aget_or_create(user_id=user_id)
    item, created = await CartItem.objects.aget_or_create(cart=cart, product_id=product_id)

    if created:
        item.quantity = quantity
    else:
        item.quantity += quantity

    await item.asave()
    await state.clear()
    await message.answer(f"✅ Добавлено в корзину. ")

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

    total = 0
    prices = []

    for item in items:
        subtotal = item.quantity * item.product.price
        total += subtotal
        prices.append(LabeledPrice(label=item.product.name, amount=int(subtotal * 100)))  # копейки

        await OrderItem.objects.acreate(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    await CartItem.objects.filter(cart=cart).adelete()

    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Оплата заказа",
        description=f"ФИО: {full_name}\nАдрес: {address}",
        payload=str(order.id),
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="order-payment"
    )

    await state.clear()

@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)

@router.message(F.content_type == "successful_payment")
async def successful_payment(message: types.Message):
    order_id = message.successful_payment.invoice_payload
    await Order.objects.filter(id=order_id).aupdate(paid=True)
    await message.answer("✅ Оплата прошла успешно! Спасибо за заказ.")

@router.callback_query(F.data.startswith("remove_"))
async def remove_from_cart(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    await state.update_data(product_id=product_id)
    await state.set_state(RemoveFromCartForm.waiting_for_remove_quantity)
    await callback.message.answer("✂️ Укажите количество товара для удаления:")

@router.message(RemoveFromCartForm.waiting_for_remove_quantity)
async def process_remove_quantity(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    product_id = data["product_id"]

    try:
        remove_qty = int(message.text)
        if remove_qty < 1:
            raise ValueError()
    except ValueError:
        await message.answer("❗ Введите корректное положительное число.")
        return

    try:
        cart = await Cart.objects.aget(user_id=user_id)
        item = await CartItem.objects.aget(cart=cart, product_id=product_id)

        if remove_qty > item.quantity:
            await message.answer(f"❗ В корзине только {item.quantity} шт. этого товара.")
            return

        if item.quantity > remove_qty:
            item.quantity -= remove_qty
            await item.asave()
            await message.answer(f"🗑️ Удалено {remove_qty} шт. товара.")
        else:
            await item.adelete()
            await message.answer("🗑️ Товар полностью удалён из корзины.")

    except CartItem.DoesNotExist:
        await message.answer("❌ Товар не найден в корзине.")

    await state.clear()
    await show_cart(message)

def register(dp):
    dp.include_router(router)

def register(dp):
    dp.include_router(router)

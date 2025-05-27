from django.contrib import admin
from .models import Category, SubCategory, Product, Cart, CartItem, Order, OrderItem, Broadcast
from django.http import HttpResponse
import openpyxl
from openpyxl import Workbook
from aiogram import Bot
import asyncio
import os
from dotenv import load_dotenv
from io import BytesIO
from asgiref.sync import sync_to_async

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "full_name", "created_at", "paid")
    actions = ["export_as_excel"]

    def export_as_excel(modeladmin, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Orders"

        ws.append(["ID", "Пользователь", "Имя", "Адрес", "Оплачен", "Создан"])

        for order in queryset:
            ws.append([
                order.id,
                order.user_id,
                order.full_name,
                order.address,
                "Да" if order.paid else "Нет",
                order.created_at.strftime("%Y-%m-%d %H:%M"),
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=orders.xlsx'

        stream = BytesIO()
        wb.save(stream)
        response.write(stream.getvalue())

        return response

    export_as_excel.short_description = "📥 Экспорт в Excel"

@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "created_at")
    actions = ["send_broadcast"]

    def send_broadcast(self, request, queryset):
        import threading

        broadcasts = list(queryset)
        user_ids = list(Order.objects.values_list("user_id", flat=True).distinct())

        def run_async_broadcast():
            asyncio.run(self._send_broadcast(broadcasts, user_ids))

        threading.Thread(target=run_async_broadcast).start()

    async def _send_broadcast(self, broadcasts, user_ids):
        bot = Bot(token=BOT_TOKEN)

        for broadcast in broadcasts:
            for uid in user_ids:
                try:
                    await bot.send_message(chat_id=uid, text=broadcast.text)
                except Exception as e:
                    print(f"Не удалось отправить сообщение {uid}: {e}")

    send_broadcast.short_description = "📨 Отправить рассылку"

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
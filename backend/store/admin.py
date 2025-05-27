from django.contrib import admin
from .models import Category, SubCategory, Product, Cart, CartItem, Order, OrderItem, Broadcast
from django.http import HttpResponse
import openpyxl
from aiogram import Bot
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "full_name", "created_at", "paid")
    actions = ["export_as_excel"]

    def export_as_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Заказы"

        headers = ["ID", "User ID", "Имя", "Адрес", "Дата", "Оплачен"]
        ws.append(headers)

        for order in queryset:
            ws.append([
                order.id,
                order.user_id,
                order.full_name,
                order.address,
                order.created_at.strftime("%Y-%m-%d %H:%M"),
                "Да" if order.paid else "Нет"
            ])

        response = HttpResponse(
            content=openpyxl.writer.excel.save_virtual_workbook(wb),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response['Content-Disposition'] = 'attachment; filename=orders.xlsx'
        return response

    export_as_excel.short_description = "📥 Экспорт в Excel"

@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "created_at")
    actions = ["send_broadcast"]

    def send_broadcast(self, request, queryset):
        async def _send():
            bot = Bot(token=BOT_TOKEN)
            for broadcast in queryset:
                user_ids = list(Order.objects.values_list("6602683327", flat=True).distinct())
                for uid in user_ids:
                    try:
                        await bot.send_message(chat_id=uid, text=broadcast.text)
                    except Exception as e:
                        print(f"Не удалось отправить сообщение {uid}: {e}")

        asyncio.run(_send())

    send_broadcast.short_description = "📨 Отправить рассылку"

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
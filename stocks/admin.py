from django.contrib import admin

from .models import StockPrice, StockWatch


@admin.register(StockWatch)
class StockWatchAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "symbol", "created_at")
    search_fields = ("symbol", "user__username")


@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    list_display = ("id", "symbol", "date", "close")
    list_filter = ("symbol",)

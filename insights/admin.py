from django.contrib import admin

from .models import AdviceLog


@admin.register(AdviceLog)
class AdviceLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    search_fields = ("user__username", "prompt", "response")

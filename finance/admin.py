from django.contrib import admin

from .models import Account, Budget, BudgetAdjustmentRequest, Category, ReceiptReview, SavingGoal, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "type", "is_active", "created_at")
    list_filter = ("type", "is_active")
    search_fields = ("name", "user__username")

#
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "is_income", "created_at")
    list_filter = ("is_income",)
    search_fields = ("name", "user__username")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "date", "type", "category", "account", "amount")
    list_filter = ("type", "date")
    search_fields = ("note", "user__username")


@admin.register(ReceiptReview)
class ReceiptReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "status", "reviewer", "created_at", "reviewed_at")
    list_filter = ("status",)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "month", "limit_amount", "created_at")
    list_filter = ("month",)

cccc
@admin.register(BudgetAdjustmentRequest)
class BudgetAdjustmentRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "budget", "new_limit_amount", "status", "created_at")
    list_filter = ("status",)


@admin.register(SavingGoal)
class SavingGoalAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "current_amount", "target_amount", "deadline", "is_completed")
    list_filter = ("is_completed",)

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Account(models.Model):
    class Type(models.TextChoices):
        CASH = "cash", "Tiền mặt"
        BANK = "bank", "Ngân hàng"
        EWALLET = "ewallet", "Ví điện tử"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=16, choices=Type.choices, default=Type.CASH)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "name")]

    def __str__(self) -> str:
        return f"{self.name}"


class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=80)
    is_income = models.BooleanField(default=False)
    icon = models.CharField(max_length=50, default="bi-tag")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "name", "is_income")]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


def receipt_upload_path(instance: "Transaction", filename: str) -> str:
    return f"receipts/user_{instance.user_id}/{filename}"


class Transaction(models.Model):
    class Type(models.TextChoices):
        INCOME = "income", "Thu"
        EXPENSE = "expense", "Chi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")

    type = models.CharField(max_length=8, choices=Type.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    date = models.DateField()
    note = models.CharField(max_length=255, blank=True)
    receipt_image = models.ImageField(upload_to=receipt_upload_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user_id} {self.type} {self.amount}"


class ReceiptReview(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Duyệt"
        REJECTED = "rejected", "Từ chối"

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="receipt_review")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="receipt_reviews"
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.transaction_id} {self.status}"


class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True, related_name="budgets")
    month = models.DateField(help_text="Ngày đầu tháng (YYYY-MM-01)")
    limit_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "category", "month")]

    def __str__(self) -> str:
        return f"{self.user_id} {self.month} {self.limit_amount}"

    @property
    def spent_amount(self):
        from django.db.models import Sum

        month_start = self.month
        month_end = (month_start.replace(day=28) + timedelta(days=4))
        month_end = month_end - timedelta(days=month_end.day)
        total = (
            Transaction.objects.filter(
                user=self.user,
                category=self.category,
                type=Transaction.Type.EXPENSE,
                date__gte=month_start,
                date__lte=month_end,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        return total

    @property
    def progress_percentage(self):
        if not self.limit_amount:
            return 0
        return min(int((self.spent_amount / self.limit_amount) * 100), 100)

    @property
    def is_over_budget(self):
        return self.spent_amount > self.limit_amount


class BudgetAdjustmentRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Duyệt"
        REJECTED = "rejected", "Từ chối"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budget_requests")
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="requests")
    new_limit_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="budget_request_reviews"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user_id} {self.status}"


class SavingGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saving_goals")
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    deadline = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.current_amount}/{self.target_amount}"

    @property
    def progress_percentage(self):
        if self.target_amount == 0:
            return 0
        return min(int((self.current_amount / self.target_amount) * 100), 100)

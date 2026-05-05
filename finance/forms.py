from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Account, Budget, BudgetAdjustmentRequest, Category, SavingGoal, Transaction


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2MB


class TransactionForm(forms.ModelForm):
    account_name = forms.CharField(
        required=False,
        max_length=120,
        label="Hoặc nhập tài khoản mới",
        widget=forms.TextInput(attrs={"placeholder": "Ví dụ: Ví tiền mặt"}),
    )
    category_name = forms.CharField(
        required=False,
        max_length=80,
        label="Hoặc nhập danh mục mới",
        widget=forms.TextInput(attrs={"placeholder": "Ví dụ: Ăn uống"}),
    )

    class Meta:
        model = Transaction
        fields = ("type", "account", "category", "amount", "date", "note", "receipt_image")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def clean_receipt_image(self):
        f = self.cleaned_data.get("receipt_image")
        if not f:
            return f
        if getattr(f, "size", 0) > MAX_UPLOAD_BYTES:
            raise ValidationError("Ảnh quá lớn (tối đa 2MB).")
        content_type = getattr(f, "content_type", "")
        if content_type and content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError("Định dạng ảnh không hợp lệ (chỉ JPG/PNG/WebP).")
        return f

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get("account")
        account_name = (cleaned_data.get("account_name") or "").strip()
        category = cleaned_data.get("category")
        category_name = (cleaned_data.get("category_name") or "").strip()

        if not account and not account_name:
            self.add_error("account", "Vui lòng chọn tài khoản hoặc nhập tài khoản mới.")
        if not category and not category_name:
            self.add_error("category", "Vui lòng chọn danh mục hoặc nhập danh mục mới.")
        return cleaned_data


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ("category", "month", "limit_amount")
        widgets = {"month": forms.DateInput(attrs={"type": "date"})}

    def clean_month(self):
        month = self.cleaned_data["month"]
        return month.replace(day=1)


class BudgetAdjustmentRequestForm(forms.ModelForm):
    class Meta:
        model = BudgetAdjustmentRequest
        fields = ("new_limit_amount", "reason")


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ("name", "type", "opening_balance", "is_active")


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "is_income", "icon")


class SavingGoalForm(forms.ModelForm):
    class Meta:
        model = SavingGoal
        fields = ("name", "target_amount", "deadline")
        widgets = {"deadline": forms.DateInput(attrs={"type": "date"})}


class SavingAddForm(forms.Form):
    amount_to_add = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0.01)


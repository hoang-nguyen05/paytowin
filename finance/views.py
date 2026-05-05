from __future__ import annotations

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from accounts.models import Profile

from .forms import BudgetForm, CategoryForm, SavingAddForm, SavingGoalForm, TransactionForm
from .models import Account, Budget, Category, SavingGoal, Transaction

DEFAULT_ACCOUNTS = [
    ("Tiền mặt", Account.Type.CASH),
    ("Ngân hàng", Account.Type.BANK),
    ("Ví điện tử", Account.Type.EWALLET),
]
DEFAULT_EXPENSE_CATEGORIES = ["Ăn uống", "Mua sắm", "Hóa đơn", "Di chuyển", "Giải trí", "Y tế"]
DEFAULT_INCOME_CATEGORIES = ["Lương", "Thưởng", "Đầu tư", "Khác"]


def ensure_default_transaction_options(user):
    for name, account_type in DEFAULT_ACCOUNTS:
        Account.objects.get_or_create(user=user, name=name, defaults={"type": account_type, "is_active": True})
    for name in DEFAULT_EXPENSE_CATEGORIES:
        Category.objects.get_or_create(user=user, name=name, is_income=False)
    for name in DEFAULT_INCOME_CATEGORIES:
        Category.objects.get_or_create(user=user, name=name, is_income=True)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name", "avatar")


class HomeView(TemplateView):
    template_name = "finance/home.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "finance/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.localdate()

        transactions = Transaction.objects.filter(user=user).select_related("category")
        income = transactions.filter(type=Transaction.Type.INCOME).aggregate(total=Sum("amount"))["total"] or 0
        expense = transactions.filter(type=Transaction.Type.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
        balance = income - expense

        context["income"] = income
        context["expense"] = expense
        context["balance"] = balance
        context["recent_transactions"] = transactions.order_by("-date", "-created_at")[:5]
        context["budgets"] = Budget.objects.filter(user=user, month=now.replace(day=1)).select_related("category")
        context["goals"] = SavingGoal.objects.filter(user=user, is_completed=False)
        return context


class StatsView(LoginRequiredMixin, TemplateView):
    template_name = "finance/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        expense_by_category = (
            Transaction.objects.filter(user=user, type=Transaction.Type.EXPENSE)
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        context["expense_by_category"] = expense_by_category
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "finance/profile.html"
    success_url = reverse_lazy("finance:profile")

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "finance/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by("is_income", "name")


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "finance/category_form.html"
    success_url = reverse_lazy("finance:category_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "finance/category_form.html"
    success_url = reverse_lazy("finance:category_list")

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "finance/category_confirm_delete.html"
    success_url = reverse_lazy("finance:category_list")

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "finance/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 10

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user).select_related("category", "account").order_by(
            "-date", "-created_at"
        )
        query = self.request.GET.get("q")
        category = self.request.GET.get("category")

        if query:
            queryset = queryset.filter(Q(note__icontains=query) | Q(amount__icontains=query))
        if category and category.isdigit():
            queryset = queryset.filter(category_id=int(category))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(user=self.request.user)
        return context


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "finance/transaction_form.html"
    success_url = reverse_lazy("finance:transaction_list")

    def get_initial(self):
        return {"date": timezone.localdate()}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        ensure_default_transaction_options(self.request.user)
        form.fields["account"].queryset = self.request.user.accounts.filter(is_active=True)
        form.fields["category"].queryset = self.request.user.categories.all()
        form.fields["account"].empty_label = "Khác (nhập bên dưới)"
        form.fields["category"].empty_label = "Khác (nhập bên dưới)"
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        account_name = (form.cleaned_data.get("account_name") or "").strip()
        category_name = (form.cleaned_data.get("category_name") or "").strip()

        if not form.cleaned_data.get("account") and account_name:
            account, _ = Account.objects.get_or_create(
                user=self.request.user,
                name=account_name,
                defaults={"type": Account.Type.CASH, "is_active": True},
            )
            form.instance.account = account
        if not form.cleaned_data.get("category") and category_name:
            category, _ = Category.objects.get_or_create(
                user=self.request.user,
                name=category_name,
                is_income=form.cleaned_data["type"] == Transaction.Type.INCOME,
            )
            form.instance.category = category
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "finance/transaction_form.html"
    success_url = reverse_lazy("finance:transaction_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        ensure_default_transaction_options(self.request.user)
        form.fields["account"].queryset = self.request.user.accounts.filter(is_active=True)
        form.fields["category"].queryset = self.request.user.categories.all()
        form.fields["account"].empty_label = "Khác (nhập bên dưới)"
        form.fields["category"].empty_label = "Khác (nhập bên dưới)"
        return form

    def form_valid(self, form):
        account_name = (form.cleaned_data.get("account_name") or "").strip()
        category_name = (form.cleaned_data.get("category_name") or "").strip()

        if not form.cleaned_data.get("account") and account_name:
            account, _ = Account.objects.get_or_create(
                user=self.request.user,
                name=account_name,
                defaults={"type": Account.Type.CASH, "is_active": True},
            )
            form.instance.account = account
        if not form.cleaned_data.get("category") and category_name:
            category, _ = Category.objects.get_or_create(
                user=self.request.user,
                name=category_name,
                is_income=form.cleaned_data["type"] == Transaction.Type.INCOME,
            )
            form.instance.category = category
        return super().form_valid(form)

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "finance/transaction_confirm_delete.html"
    success_url = reverse_lazy("finance:transaction_list")

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = "finance/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        now = timezone.localdate().replace(day=1)
        return Budget.objects.filter(user=self.request.user, month=now).select_related("category")


class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = "finance/budget_form.html"
    success_url = reverse_lazy("finance:budget_list")

    def get_initial(self):
        return {"month": timezone.localdate().replace(day=1)}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["category"].queryset = self.request.user.categories.filter(is_income=False)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.month = timezone.localdate().replace(day=1)
        return super().form_valid(form)


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = "finance/budget_form.html"
    success_url = reverse_lazy("finance:budget_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["category"].queryset = self.request.user.categories.filter(is_income=False)
        return form

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    model = Budget
    template_name = "finance/budget_confirm_delete.html"
    success_url = reverse_lazy("finance:budget_list")

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


class SavingGoalListView(LoginRequiredMixin, ListView):
    model = SavingGoal
    template_name = "finance/goal_list.html"
    context_object_name = "goals"

    def get_queryset(self):
        return SavingGoal.objects.filter(user=self.request.user).order_by("-created_at")


class SavingGoalCreateView(LoginRequiredMixin, CreateView):
    model = SavingGoal
    form_class = SavingGoalForm
    template_name = "finance/goal_form.html"
    success_url = reverse_lazy("finance:goal_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class SavingGoalUpdateView(LoginRequiredMixin, UpdateView):
    model = SavingGoal
    form_class = SavingGoalForm
    template_name = "finance/goal_form.html"
    success_url = reverse_lazy("finance:goal_list")

    def get_queryset(self):
        return SavingGoal.objects.filter(user=self.request.user)


class SavingGoalDeleteView(LoginRequiredMixin, DeleteView):
    model = SavingGoal
    template_name = "finance/goal_confirm_delete.html"
    success_url = reverse_lazy("finance:goal_list")

    def get_queryset(self):
        return SavingGoal.objects.filter(user=self.request.user)


class SavingGoalAddView(LoginRequiredMixin, UpdateView):
    model = SavingGoal
    form_class = SavingAddForm
    template_name = "finance/goal_add_saving.html"
    success_url = reverse_lazy("finance:goal_list")

    def get_queryset(self):
        return SavingGoal.objects.filter(user=self.request.user)

    def form_valid(self, form):
        amount = form.cleaned_data["amount_to_add"]
        self.object.current_amount += amount
        if self.object.current_amount >= self.object.target_amount:
            self.object.is_completed = True
        self.object.save()
        return redirect(self.success_url)

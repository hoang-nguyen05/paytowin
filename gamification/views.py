from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from finance.models import Transaction

from .models import Badge, UserBadge


@login_required
def dashboard(request):
    today = timezone.localdate()
    month = today.replace(day=1)
    qs = Transaction.objects.filter(user=request.user, date__gte=month, date__lte=today)
    income = qs.filter(type=Transaction.Type.INCOME).aggregate(t=Sum("amount"))["t"] or 0
    expense = qs.filter(type=Transaction.Type.EXPENSE).aggregate(t=Sum("amount"))["t"] or 0
    saving = float(income - expense)
    saving_rate = (saving / float(income) * 100) if income else 0.0

    level = 1
    if saving_rate >= 30:
        level = 5
    elif saving_rate >= 20:
        level = 4
    elif saving_rate >= 10:
        level = 3
    elif saving_rate > 0:
        level = 2

    # Award simple badges
    b1, _ = Badge.objects.get_or_create(code="first_steps", defaults={"name": "First Steps", "description": "Có giao dịch đầu tiên"})
    b2, _ = Badge.objects.get_or_create(code="budget_master", defaults={"name": "Budget Master", "description": "Tiết kiệm >= 20% trong tháng"})

    if Transaction.objects.filter(user=request.user).exists():
        UserBadge.objects.get_or_create(user=request.user, badge=b1)
    if saving_rate >= 20:
        UserBadge.objects.get_or_create(user=request.user, badge=b2)

    earned = UserBadge.objects.filter(user=request.user).select_related("badge").order_by("-earned_at")
    return render(
        request,
        "gamification/dashboard.html",
        {"level": level, "saving_rate": saving_rate, "earned": earned[:20]},
    )

from django.shortcuts import render

# Create your views here.

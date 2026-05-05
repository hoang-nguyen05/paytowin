from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from finance.models import Transaction

from .forms import RegisterForm


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    now = timezone.localdate()
    month_start = now.replace(day=1)

    qs = Transaction.objects.filter(user=request.user, date__gte=month_start, date__lte=now)
    income = qs.filter(type=Transaction.Type.INCOME).aggregate(total=Sum("amount"))["total"] or 0
    expense = qs.filter(type=Transaction.Type.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
    balance = income - expense

    recent = qs.order_by("-date", "-id")[:8]
    return render(
        request,
        "accounts/dashboard.html",
        {"income": income, "expense": expense, "balance": balance, "recent": recent},
    )

from django.shortcuts import render

# Create your views here.
def dashbooassrd(request):
    return render(request, "accounts/dashboard.html")
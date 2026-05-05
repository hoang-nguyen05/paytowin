from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from random import choice, randint

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from finance.models import Account, Budget, Category, Transaction


class Command(BaseCommand):
    help = "Seed demo data (users, categories, transactions, budgets)."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username="demo", defaults={"email": "demo@example.com"})
        if created:
            user.set_password("demo12345")
            user.save()

        admin, created_admin = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com", "is_staff": True})
        if created_admin:
            admin.set_password("admin12345")
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        acc_cash, _ = Account.objects.get_or_create(user=user, name="Tiền mặt", defaults={"type": Account.Type.CASH})
        acc_bank, _ = Account.objects.get_or_create(user=user, name="Ngân hàng", defaults={"type": Account.Type.BANK})

        expense_names = ["Ăn uống", "Mua sắm", "Hoá đơn", "Giải trí", "Di chuyển", "Y tế"]
        income_names = ["Lương", "Thưởng", "Khác"]

        for n in expense_names:
            Category.objects.get_or_create(user=user, name=n, is_income=False)
        for n in income_names:
            Category.objects.get_or_create(user=user, name=n, is_income=True)

        cats_exp = list(Category.objects.filter(user=user, is_income=False))
        cats_inc = list(Category.objects.filter(user=user, is_income=True))

        today = timezone.localdate()
        start = today - timedelta(days=90)

        if not Transaction.objects.filter(user=user).exists():
            # Seed incomes (weekly)
            d = start
            while d <= today:
                if d.weekday() == 0:
                    Transaction.objects.create(
                        user=user,
                        account=acc_bank,
                        category=choice(cats_inc),
                        type=Transaction.Type.INCOME,
                        amount=Decimal(randint(7000000, 15000000)),
                        date=d,
                        note="Thu nhập (demo)",
                    )
                d += timedelta(days=1)

            # Seed expenses (daily)
            d = start
            while d <= today:
                for _ in range(randint(0, 2)):
                    Transaction.objects.create(
                        user=user,
                        account=choice([acc_cash, acc_bank]),
                        category=choice(cats_exp),
                        type=Transaction.Type.EXPENSE,
                        amount=Decimal(randint(20000, 500000)),
                        date=d,
                        note="Chi tiêu (demo)",
                    )
                d += timedelta(days=1)

        month = today.replace(day=1)
        for c in cats_exp[:4]:
            Budget.objects.get_or_create(
                user=user,
                category=c,
                month=month,
                defaults={"limit_amount": Decimal(randint(1500000, 3500000))},
            )

        self.stdout.write(self.style.SUCCESS("Seeded demo. Login: demo/demo12345, admin/admin12345"))


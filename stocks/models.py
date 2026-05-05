from django.conf import settings
from django.db import models


class StockWatch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stock_watches")
    symbol = models.CharField(max_length=24, help_text="Ví dụ: aapl.us (Stooq) hoặc VNM.VN (tuỳ nguồn)")
    note = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "symbol")]

    def __str__(self) -> str:
        return self.symbol


class StockPrice(models.Model):
    symbol = models.CharField(max_length=24)
    date = models.DateField()
    close = models.DecimalField(max_digits=14, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("symbol", "date")]
        indexes = [models.Index(fields=["symbol", "-date"])]

    def __str__(self) -> str:
        return f"{self.symbol} {self.date}"

from __future__ import annotations

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import StockPrice, StockWatch
from .services import (
    fetch_stooq_daily_csv,
    fetch_yahoo_daily_rows,
    fetch_yahoo_intraday_closes,
    fetch_yahoo_quote,
    moving_average_forecast,
    normalize_symbol_for_yahoo,
)


@login_required
def dashboard(request):
    watches = StockWatch.objects.filter(user=request.user).order_by("symbol")
    default_symbols = ["VNINDEX", "FPT.VN", "VNM.VN", "AAPL", "MSFT", "NVDA", "BTC-USD", "ES=F"]
    return render(request, "stocks/dashboard.html", {"watches": watches, "default_symbols": default_symbols})


@login_required
def add_watch(request):
    if request.method == "POST":
        symbol = (request.POST.get("symbol") or "").strip().upper()
        note = (request.POST.get("note") or "").strip()
        if symbol:
            StockWatch.objects.get_or_create(user=request.user, symbol=symbol, defaults={"note": note})
            messages.success(request, "Đã thêm mã theo dõi.")
    return redirect("stocks:dashboard")


@login_required
def delete_watch(request, pk: int):
    w = get_object_or_404(StockWatch, pk=pk, user=request.user)
    if request.method == "POST":
        w.delete()
        messages.info(request, "Đã xoá.")
    return redirect("stocks:dashboard")


@login_required
def symbol_detail(request, symbol: str):
    error = None
    rows: list[tuple[str, float]] = fetch_yahoo_daily_rows(symbol, range_="6mo")
    try:
        if not rows:
            rows = fetch_stooq_daily_csv(symbol)
    except Exception:
        pass

    if not rows:
        # fallback: use cached DB last 60 days
        error = "Không lấy được dữ liệu online. Đang hiển thị dữ liệu cache (nếu có)."
        prices = (
            StockPrice.objects.filter(symbol=symbol)
            .order_by("-date")[:60]
        )
        rows = [(p.date.strftime("%Y-%m-%d"), float(p.close)) for p in reversed(list(prices))]
    else:
        # Cache last 180 days into DB
        for d, c in rows[-180:]:
            StockPrice.objects.update_or_create(
                symbol=symbol,
                date=datetime.strptime(d, "%Y-%m-%d").date(),
                defaults={"close": c},
            )

    closes = [c for _, c in rows]
    forecast = moving_average_forecast(closes, window=10)
    last_close = closes[-1] if closes else None
    change_1d = (closes[-1] - closes[-2]) if len(closes) >= 2 else None
    change_7d = (closes[-1] - closes[-8]) if len(closes) >= 8 else None
    min60 = min(closes[-60:]) if closes else None
    max60 = max(closes[-60:]) if closes else None
    trend = "Tăng" if (change_7d or 0) > 0 else "Giảm/đi ngang"

    return render(
        request,
        "stocks/symbol_detail.html",
        {
            "symbol": symbol,
            "rows": rows[-60:],
            "forecast": forecast,
            "last_close": last_close,
            "change_1d": change_1d,
            "change_7d": change_7d,
            "min60": min60,
            "max60": max60,
            "trend": trend,
            "error": error,
        },
    )


@login_required
def board_data(request):
    default_symbols = ["VNINDEX", "FPT.VN", "VNM.VN", "AAPL", "MSFT", "NVDA", "BTC-USD", "ES=F"]
    watched = [w.symbol for w in StockWatch.objects.filter(user=request.user).order_by("symbol")]
    symbols = watched or default_symbols

    rows = []
    for symbol in symbols:
        q = fetch_yahoo_quote(symbol)
        intraday = fetch_yahoo_intraday_closes(symbol, interval="5m", range_="1d")
        if not q and not intraday:
            continue
        price = q.get("price") if q else None
        prev = q.get("previous_close") if q else None
        if price is None and intraday:
            price = intraday[-1]
        if prev is None and len(intraday) >= 2:
            prev = intraday[0]
        change = (price - prev) if (price is not None and prev not in (None, 0)) else (q.get("change") if q else None)
        change_percent = (
            (change / prev * 100) if (change is not None and prev not in (None, 0)) else (q.get("change_percent") if q else None)
        )
        rows.append(
            {
                "symbol": normalize_symbol_for_yahoo(symbol),
                "name": q.get("name") if q else normalize_symbol_for_yahoo(symbol),
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "open": q.get("open") if q else None,
                "high": q.get("high") if q else (max(intraday) if intraday else None),
                "low": q.get("low") if q else (min(intraday) if intraday else None),
                "volume": q.get("volume") if q else None,
                "spark": intraday[-40:],
            }
        )
    return JsonResponse({"rows": rows})

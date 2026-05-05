from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from finance.models import Transaction

from .models import AdviceLog
from .services import fallback_advice, ollama_chat


@login_required
def advisor(request):
    today = timezone.localdate()
    start = today - timedelta(days=30)
    qs = Transaction.objects.filter(user=request.user, date__gte=start, date__lte=today)

    total_income = qs.filter(type=Transaction.Type.INCOME).aggregate(t=Sum("amount"))["t"] or 0
    total_expense = qs.filter(type=Transaction.Type.EXPENSE).aggregate(t=Sum("amount"))["t"] or 0
    top_expense = (
        qs.filter(type=Transaction.Type.EXPENSE)
        .values("category__name")
        .annotate(t=Sum("amount"))
        .order_by("-t")[:5]
    )
    top_lines = "\n".join([f"- {x['category__name']}: {x['t']}" for x in top_expense]) or "- (chưa có)"
    summary = (
        f"30 ngày gần nhất:\n"
        f"- Tổng thu: {total_income}\n"
        f"- Tổng chi: {total_expense}\n"
        f"- Top chi theo danh mục:\n{top_lines}\n"
    )

    prompt = (
        "Bạn là trợ lý tài chính cá nhân. "
        "Hãy phân tích thói quen chi tiêu và đưa gợi ý tiết kiệm cụ thể, ngắn gọn, theo bullet. "
        "Nhắc nhở các khoản chi bất thường nếu thấy dấu hiệu. "
        "Luôn có phần 'Kế hoạch tháng tới' gồm các bước hành động theo tuần.\n\n"
        f"Dữ liệu:\n{summary}"
    )

    import os

    # Luôn tạo phản hồi mặc định theo dữ liệu mới nhất để tránh hiển thị dữ liệu cũ.
    response = fallback_advice(summary)
    ai_called = False
    using_fallback = False
    if request.method == "POST":
        user_question = (request.POST.get("question") or "").strip()
        if user_question:
            prompt = (
                f"{prompt}\n\n"
                f"Câu hỏi thêm của người dùng: {user_question}\n"
                "Trả lời trực tiếp câu hỏi và gắn với dữ liệu chi tiêu ở trên."
            )
        ai_called = True
        response = ollama_chat(
            model=os.environ.get("OLLAMA_MODEL", "llama3.2"),
            prompt=prompt,
            timeout_seconds=float(os.environ.get("OLLAMA_TIMEOUT", "45")),
        )
        if not response:
            response = fallback_advice(summary)
            using_fallback = True
        AdviceLog.objects.create(user=request.user, prompt=prompt, response=response)
    else:
        user_question = ""

    # Dự đoán chi tiêu tháng tới (baseline: trung bình 3 tháng gần nhất)
    month0 = today.replace(day=1)
    months = [month0]
    for _ in range(2):
        prev = (months[-1] - timedelta(days=1)).replace(day=1)
        months.append(prev)
    expenses = []
    for m in months:
        m_end = (m.replace(day=28) + timedelta(days=4))
        m_end = m_end - timedelta(days=m_end.day)
        total = (
            Transaction.objects.filter(user=request.user, type=Transaction.Type.EXPENSE, date__gte=m, date__lte=m_end)
            .aggregate(t=Sum("amount"))["t"]
            or 0
        )
        expenses.append(float(total))
    predicted_next_month_expense = round(sum(expenses) / max(len(expenses), 1), 2)
    plan_next_month = [
        f"Tuần 1: đặt trần chi tiêu tổng tháng ở mức khoảng {predicted_next_month_expense:,.0f}.",
        "Tuần 2: rà soát top 3 danh mục chi nhiều nhất, giảm ít nhất 10% từng danh mục.",
        "Tuần 3: kiểm tra chi tiêu bất thường và cắt các khoản không cần thiết.",
        "Tuần 4: tổng kết, so sánh với kế hoạch, điều chỉnh ngân sách cho tháng kế tiếp.",
    ]

    return render(
        request,
        "insights/advisor.html",
        {
            "summary": summary,
            "response": response,
            "predicted_next_month_expense": predicted_next_month_expense,
            "ai_called": ai_called,
            "using_fallback": using_fallback,
            "user_question": user_question,
            "plan_next_month": plan_next_month,
        },
    )

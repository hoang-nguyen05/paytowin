# Quản lý chi tiêu thông minh (Django)

Hệ thống web **ghi chép – phân tích – gợi ý tài chính cá nhân**, có dashboard, báo cáo biểu đồ, quản lý ngân sách, workflow duyệt (Admin), tích hợp AI (Llama 3.2 qua Ollama) và demo dự đoán chứng khoán.

## Công nghệ

- Python + Django (Template + Bootstrap + Chart.js)
- CSDL: SQLite (mặc định, dễ chạy demo)
- Upload ảnh: Pillow

## Chức năng chính (đáp ứng rubric)

- **Xác thực & phân quyền**: đăng ký, đăng nhập, quên mật khẩu (email console), phân quyền Admin qua `is_staff`.
- **CRUD**:
  - Giao dịch thu/chi (`Transaction`) + tìm kiếm/lọc/sắp xếp
  - Ngân sách (`Budget`) + tiến độ sử dụng
- **2 luồng nghiệp vụ có trạng thái**:
  - Duyệt hoá đơn: `ReceiptReview` (pending/approved/rejected)
  - Duyệt yêu cầu điều chỉnh ngân sách: `BudgetAdjustmentRequest` (pending/approved/rejected)
- **Thống kê – báo cáo**: biểu đồ tròn theo danh mục + biểu đồ cột thu/chi theo tháng.
- **Upload ảnh an toàn**: giới hạn 2MB, chỉ JPG/PNG/WebP.
- **AI advisor**: gọi Ollama model `llama3.2` (fallback nếu chưa chạy Ollama).
- **Dự đoán chi tiêu tháng tới**: baseline trung bình 3 tháng gần nhất.
- **Gamification**: level + huy hiệu cơ bản.
- **Stock demo**: watchlist + lấy dữ liệu Stooq + dự đoán MA10.

## Thực thể dữ liệu (>=5) & quan hệ

- `auth.User` (Django)
- `accounts.Profile` (1-1 User)
- `finance.Account` (n-1 User)
- `finance.Category` (n-1 User)
- `finance.Transaction` (n-1 User, FK Account/Category) + ảnh hoá đơn
- `finance.Budget` (n-1 User, FK Category)
- `finance.ReceiptReview` (1-1 Transaction, workflow trạng thái)
- `finance.BudgetAdjustmentRequest` (n-1 Budget, workflow trạng thái)
- `insights.AdviceLog` (n-1 User)
- `stocks.StockWatch`, `stocks.StockPrice`
- `gamification.Badge`, `gamification.UserBadge`

## Cài đặt & chạy

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Mở web: `http://127.0.0.1:8000/`

## Tài khoản mẫu

- User demo: `demo` / `demo12345`
- Admin: `admin` / `admin12345`
- Admin workflow page: `http://127.0.0.1:8000/finance/admin/workflows/`

## Kết nối Llama 3.2 (tuỳ chọn)

Nếu bạn có Ollama:

```bash
ollama run llama3.2
```

Tạo file `.env` tại thư mục dự án (cùng cấp `manage.py`) để cấu hình:

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

App sẽ gọi `http://localhost:11434/api/generate`. Bạn có thể thay model hoặc URL trong `.env`.


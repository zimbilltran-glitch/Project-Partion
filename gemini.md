# 🧠 Finsang Project Constitution (v5.1.x)

Dài liệu Hiến pháp và Quy tắc tối thượng dành cho các AI Agent tham gia phát triển dự án Finsang. Mọi Agent khi vào project PHẢI đọc và tuân thủ các nguyên tắc này.

---

## 🏛️ Project Identity & Directory Structure
Dự án được cấu trúc theo triết lý "Clean State", tách biệt code vận hành (Production) và code khảo sát (Archive).

- **Root**: Các tài liệu Master Control (`README.md`, `Finsang_Master_*.md`).
- **`sub-projects/Version_2`**: Trái tim của dự án (Core Engine). Chứa Pipeline, Security và Metrics.
- **`sub-projects/V5_improdata`**: Performance & Data Integrity. Chứa resync async và run metrics batch.
- **`archive_legacy`**: Nơi lưu trữ toàn bộ code cũ, log và data nháp. **Agent phải kiểm tra đây nếu không tìm thấy script cũ.**

---

## 🛡️ Core Behavioral Rules for Agents

### 1. Data Integrity: **Exact Ground Truth Mapping**
- **KHÔNG** bao giờ sử dụng mapping theo vị trí hàng (Relative Index/Enumerate) khi làm việc với Vietcap API.
- **LUÔN** sử dụng `vietcap_key` (Ví dụ: `isa1`, `bsa20`) được map cứng theo tên dòng (`name`) đã đối chiếu với BCTC kiểm toán.
- Bất kỳ thay đổi schema nào cũng phải cập nhật vào `golden_schema.json` và `lite_schema.json`.

### 2. Performance: **Async & Lite First**
- Sử dụng `ThreadPoolExecutor` cho các tác vụ lặp lại (Resync 30-100 mã).
- Ưu tiên sử dụng `lite_schema.json` (<200KB) thay vì `golden_schema.json` (>700KB) để tiết kiệm tài nguyên.
- Thời gian resync VN30 mục tiêu: **< 30 giây.**

### 3. Security: **Strict Hardening**
- **TIMEOUT**: Mọi lệnh `requests` PHẢI có `timeout=10`.
- **CREDENTIALS**: Tuyệt đối không commit file `.env` hoặc keys thô lên Git.
- **RLS**: Mọi bảng mới trong Supabase phải có Row Level Security. `anon` chỉ có quyền `SELECT`.

### 4. Code Hygiene: **Atomic & Modulized**
- Code phải tách biệt giữa logic Fetcher (Providers), Processor (Pipeline/Metrics) và Storage (Supabase).
- Sử dụng `sb_client.py` (Singleton) để quản lý kết nối database, tránh Pooling Exhaustion.

---

## 📊 Data Standard Invariants
- **Database**: Supabase Cloud là Source of Truth duy nhất cho Production.
- **LocalStorage**: Thư mục `data/` chứa file Parquet mã hóa AES-128, dùng làm buffer tính toán locally. **Tuyệt đối không đẩy lên Git.**
- **Currency**: Tất cả số liệu hiển thị trên Web phải được định dạng theo tiêu chuẩn Vietcap (Tr CP, Tỷ VND).

---

## 📎 Reference Master Docs
- 📑 [Finsang Master Team Guide](Finsang_Master_Team_Guide.md)
- 🚀 [Finsang Master Active Roadmap](Finsang_Master_Active_Roadmap.md)
- 📘 [QUARTERLY UPDATE GUIDE](QUARTERLY_UPDATE_GUIDE.md)

---
*Constitution updated at 2026-03-05 | Authorized by Antigravity CTO Agent.*

# V3 Challenges & Solutions

> Ghi nhận các thách thức gặp phải và giải pháp.

---

## C-001: OHLCV Volume vs API Rate Limit

**Challenge**: Fetch OHLCV daily cho 30 tickers × 365 ngày × 2 năm = ~21,900 API calls.  
**Risk**: Token overuse / API throttling từ Vietcap.

**Solution**: 
- Batch fetch: 1 request = full history per ticker (Vietcap trả multi-row per request)
- Rate limit: 0.5s delay between tickers
- Scope: Chỉ fetch 2025-01-01 đến nay (giảm ~50% volume)
- Fallback: Nếu Vietcap bị chặn → dùng VNDirect hoặc TCBS API

## C-002: Cross-Platform Chart Compatibility

**Challenge**: Chart phải chạy được cả Vite (React) và Streamlit (Python).  
**Solution**: Dùng Plotly.js — là thư viện duy nhất hoạt động natively trên cả hai:
- React: `react-plotly.js`
- Streamlit: `st.plotly_chart(fig)`
- Cùng data format (JSON traces), dễ chuyển đổi.

**Updated Solution**: Sau khi research, quyết định dùng **Pure SVG** code cứng cho Snowflake và Price Chart để tối ưu tải trang về 0 KB dependency, rất phù hợp với Dashboard React.

## C-003: Supabase RLS (Row Level Security) Permission Denied
**Challenge**: Khi script backend tự động ghi vào bảng `company_overview`, bị Supabase block do vi phạm RLS (cụ thể là HTTP 403 Forbidden).
**Solution**: Viết SQL migration scripts tạo `anon_insert` và `anon_update` policy cho roles `anon`.

## C-004: Windows Console CP1252 Encoding Issues
**Challenge**: Khi chạy lệnh in tiến trình ra Windows console (PowerShell), các emoji (✅, ❌) hoặc ký hiệu mũi tên (→) làm script Python crash do lỗi `UnicodeEncodeError: 'charmap' codec can't encode character`.
**Solution**: Thay các emoji này bằng format chữ trong CLI: `[OK]`, `[FAIL]`, `[SKIP]`, và đổi `→` thành `->` hoặc `=>`.

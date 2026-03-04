# 🚧 V5 Challenges & Issues Log

Theo dõi các khó khăn kỹ thuật và hướng giải quyết trong quá trình làm V5, để agent đi sau nắm bắt tình hình.

## 1. Sequential Mapping Fail ⚠️ RESOLVED

- **Tình trạng**: ✅ Đã giải quyết
- **Chẩn đoán**: Ban đầu giả định `bsa[sorted_index]` → `field[index]` (sequential). Giả định SAI vì:
  - Schema golden_schema.json có **65 fields** trước "TỔNG CỘNG TÀI SẢN" (do có nhiều sub-items chi tiết)
  - Vietcap API chỉ có **52 keys** (bsa1-bsa52) cho phần Assets
  - Kết quả: field[65] (Tổng TS) bị map sang bsa66 thay vì bsa53 → **sai giá trị**
- **Giải pháp**: **Segmented mapping** — chia CDKT thành 5 segments:
  1. Assets (field[0..64]) → bsa1..bsa52 (13 fields dư không có key)
  2. Total Assets (field[65]) → bsa53 (anchor từ Bank schema)
  3. Liabilities (field[66..96]) → bsa54..bsa77
  4. Equity (field[97..120]) → bsa78..bsa95 + bsa159+
  5. Total Source (field[121]) → bsa96

## 2. Xử lý key gaps ✅ RESOLVED

- **Tình trạng**: ✅ Đã giải quyết
- **Chẩn đoán**: Keys bsa1-bsa96 **KHÔNG CÓ gap** (96 keys liên tục). Gap chỉ xảy ra sau bsa96 (nhảy sang bsa159). Block phụ: 159-178, 188, 209-211, 276-278.
- **Giải pháp**: Chia pool theo segment (block chính 1-96 + block phụ 159+) thay vì sort tất cả chung.

## 3. Hardcoded field_mapping sai ⚠️ RESOLVED

- **Tình trạng**: ✅ Đã xóa hoàn toàn
- **Chẩn đoán**: 10 hardcoded overrides trong `vietcap.py`, trong đó **6/10 SAI**:
  - `cdkt_tong_cong_tai_san → bsa96` ❌ (correct: bsa53)
  - `cdkt_tai_san_dai_han → bsa23` ❌ (correct: bsa27)
  - `cdkt_von_chu_so_huu → bsa79` ❌ (correct: bsa78)
  - `cdkt_no_ngan_han → bsa55` ✅ (correct)
  - `kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me → isa22` → (correct: isa23)
- **Giải pháp**: Xóa toàn bộ `field_mapping` dict. Xóa fallback `f"bsa{idx}"`. Mọi field đều dùng explicit `vietcap_key` từ `golden_schema.json`.

## 4. Terminal encoding (Windows cp1252) ✅ KNOWN

- **Tình trạng**: Biết rõ, workaround đã có
- **Chẩn đoán**: PowerShell mặc định dùng cp1252, không hiển thị được tiếng Việt Unicode.
- **Giải pháp**: Tất cả Python output phải write to file (`encoding='utf-8'`), không `print()` trực tiếp. Hoặc set `$env:PYTHONIOENCODING='utf-8'` trước run.

## 5. Vietcap API Rate Limiting ⚠️ NOTED

- **Tình trạng**: Noted, chưa gặp vấn đề
- **Chẩn đoán**: API công khai, không cần auth, nhưng có thể giới hạn request nếu fetch quá nhiều ticker liên tục.
- **Giải pháp**: Thêm `time.sleep(1)` giữa mỗi ticker khi chạy batch VN30.

## 6. Schema fields > API keys (Assets mismatch) ⚠️ ACCEPTED

- **Tình trạng**: Accepted — không phải bug
- **Chẩn đoán**: Golden schema có **65 fields** cho phần Tài sản (theo TT200), nhưng Vietcap API chỉ có **52 keys** (bsa1-bsa52). 13 fields dư (e.g., "Tài sản thiếu cần xử lý", "Giao dịch mua bán lại trái phiếu CP") không có giá trị từ API.
- **Giải pháp**: Các field dư giữ `vietcap_key: ""` → pipeline trả về `null` cho các field này. Đây là hành vi đúng (Vietcap không cung cấp dữ liệu cho sub-items này).

## 7. NOTE section không có API data ⚠️ ACCEPTED

- **Tình trạng**: Accepted — không phải bug
- **Chẩn đoán**: Vietcap API endpoint `/financial-statement?section=NOTE` trả về JSON nhưng **0 non-null `noa`/`nob` keys**. 157 NOTE fields không có dữ liệu.
- **Giải pháp**: NOTE sheet giữ nguyên `vietcap_key: ""`. Dữ liệu NOTE cần tìm nguồn khác nếu cần thiết.

## 8. Vietcap website blocked by HTTP fetch ⚠️ WORKAROUND

- **Tình trạng**: Workaround found
- **Chẩn đoán**: `read_url_content` trả về HTTP 403 khi truy cập `trading.vietcap.com.vn`. Trang web dùng SPA (React) nên content chỉ có qua JavaScript rendering.
- **Giải pháp**: Dùng **Bank schema ground truth** (đã có correct mapping) để xác nhận anchor points thay vì scrape web. Bank fields dùng `bsa` prefix cho shared items → cùng key number cho normal company.
## 9. Local Frontend Hosting (npm permissions & recharts) ✅ RESOLVED

- **Tình trạng**: ✅ Đã giải quyết
- **Chẩn đoán**: Khi host lại frontend tại local, gặp lỗi:
  - `UnauthorizedAccess` trên PowerShell do Policy chặn chạy script `npm`.
  - Thiếu package `recharts` (mặc dù có trong `package.json`).
- **Giải pháp**: 
  - Dùng `powershell -ExecutionPolicy Bypass` để chạy `npm install` và `npm run dev`
 - Explicitly `npm install recharts` để fix lỗi Vite build error.
## 10. Unit Mismatch in Parquet Data (Phase 5) ✅ RESOLVED

- **Tình trạng**: ✅ Đã giải quyết bằng cách dùng `metrics.py` thuần.
- **Chẩn đoán**: Script `calculate_cstc.py` bị lỗi unit giữa Tỷ VND (LNST) và VND đồng (Vốn CSH).
- **Giải pháp**: Ngừng sử dụng `calculate_cstc.py`, quay lại dùng engine `metrics.py` vốn đã có logic handle unit chuẩn xác từ Supabase.

## 11. Import Chain Hang (Security/Cipher) ✅ RESOLVED

- **Tình trạng**: ✅ Đã giải quyết
- **Chẩn đoán**: Treo do dependencies phức tạp trong `pipeline.py`.
- **Giải pháp**: Viết script batch độc lập `run_metrics_batch.py` chỉ import `calc_metrics` từ `metrics_debug.py` để cô lập logic.

## 12. Supabase Client Hang in Loops ✅ RESOLVED

- **Tình trạng**: ✅ Đã giải quyết
- **Chẩn đoán**: Khi loop qua 30 mã và khởi tạo `supabase.create_client` mỗi lần, resource bị cạn kiệt hoặc pool bị block khiến lệnh `.execute()` treo vô hạn.
- **Giải pháp**: Triển khai **Singleton Pattern** trong `sb_client.py` để tái sử dụng một instance duy nhất xuyên suốt quá trình chạy batch.

## 13. Positional Mapping Anti-Pattern (Catastrophic) ✅ RESOLVED

- **Tình trạng**: ✅ Đã giải quyết (Phase 5.3)
- **Chẩn đoán**: Keys API (`isaX`, `bsaX`) là các index chỉ định vị trí dòng, không phải định danh duy nhất. Khi các công ty có cấu trúc BCTC khác nhau (thiếu/thừa dòng), các keys sẽ bị "trượt" (shift), làm sai lệch hoàn toàn ý nghĩa dữ liệu (ví dụ EPS bị map nhầm vào Lợi nhuận ròng).
- **Giải pháp**: 
  - Đã từ bỏ phương pháp dò tự động. Chuyển sang dùng **Exact Ground Truth Map**. Cụ thể: đối chiếu trực tiếp dữ liệu thô với BCTC thật mà CFO xác nhận (ảnh Excel user). 
  - Khóa chặt ~22 các field core (`isa20` cho Lãi ròng, `isb27` cho Thu nhập lãi thuần, v.v.) vào `golden_schema.json`.
  - Xóa toàn bộ dữ liệu Supabase bị hỏng và chạy `v5_full_resync.py` để làm phẳng lại toàn bộ 31 mã.


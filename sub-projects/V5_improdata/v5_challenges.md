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

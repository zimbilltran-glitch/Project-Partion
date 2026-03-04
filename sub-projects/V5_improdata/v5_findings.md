# 🔎 V5 Data Findings Log

Nơi ghi chú nhanh các phát hiện về cấu trúc dữ liệu, lỗi mapping, và thông tin API trong khuôn khổ dự án V5.

## 1. Hệ thống Key Prefix của Vietcap API

Vietcap API sử dụng **multi-prefix key system**. Mỗi section có nhiều prefix khác nhau:

### Balance Sheet (BALANCE_SHEET)
| Prefix | Ý nghĩa | Range | Áp dụng cho |
|--------|---------|-------|-------------|
| `bsa`  | ALL items (Assets + Liab + Equity) cho Normal | 1-96 chính + 159-278 phụ | Normal company |
| `bsb`  | Bank-specific items | 97-263 | Ngân hàng |
| `bss`  | Securities sector | 133-257 | Chỉ CTCK |
| `bsi`  | Insurance sector | 139-287 | Chỉ Bảo hiểm |

> ⚠️ **QUAN TRỌNG**: `bsa` KHÔNG phải chỉ là "Assets". Đối với normal company, `bsa` chứa
> TẤT CẢ dòng BCTC (Tài sản + Nợ phải trả + Vốn CSH + Tổng nguồn vốn).
> Bank thì dùng `bsa` cho shared items + `bsb` cho bank-specific items.

### Income Statement (INCOME_STATEMENT)
| Prefix | Ý nghĩa | Áp dụng cho |
|--------|---------|-------------|
| `isa`  | Normal IS items | Normal company (25 keys: isa1-isa24 + isa102) |
| `isb`  | Bank-specific IS items | Ngân hàng |
| `iss`  | Securities-specific | CTCK |

### Cash Flow (CASH_FLOW)
| Prefix | Ý nghĩa | Áp dụng cho |
|--------|---------|-------------|
| `cfa`  | Normal CF items | Normal company (48 keys: cfa1-cfa45 + cfa103-105) |
| `cfb`  | Bank CF items | Ngân hàng |
| `cfs`  | Securities CF items | CTCK |

---

## 2. Cấu trúc BS Key cho Normal Company (CDKT)

### 🔑 PHÁT HIỆN QUAN TRỌNG (Phase 2)

**bsa keys cho FPT (normal) có 123 non-null keys, chia thành 2 block:**
- **Block chính**: `bsa1`..`bsa96` — **96 keys liên tục, KHÔNG có gap**
- **Block phụ**: `bsa159, 160, ..., 178, 188, 209, 210, 211, 276, 277, 278` — **27 keys**

**Cấu trúc logic (segment) bên trong 96 key chính:**

| Segment | Key Range | Ý nghĩa | Ghi chú |
|---------|-----------|---------|---------|
| Assets  | bsa1 → bsa52 | 52 mục tài sản | TÀI SẢN NGẮN HẠN (bsa1), TÀI SẢN DÀI HẠN (bsa27) |
| **Total Assets** | **bsa53** | **TỔNG CỘNG TÀI SẢN** | ✅ Confirmed via Bank schema anchor |
| Liabilities | bsa54 → bsa77 | 24 mục nợ phải trả | NỢ PHẢI TRẢ (bsa54), Nợ ngắn hạn (bsa55) |
| Equity | bsa78 → bsa95 | 18 mục vốn CSH | VỐN CHỦ SỞ HỮU (bsa78) |
| **Total Source** | **bsa96** | **NỢ PHẢI TRẢ VÀ VỐN CSH** | = Tổng nguồn vốn |

**Block phụ (bsa159+)**: Các mục bổ sung Equity (Vốn góp chi tiết, LNST phân phối, CĐ thiểu số...).

### Anchor Points xác nhận từ Bank Schema (Ground Truth)
| Key | Giá trị FPT 2024 | Tên field |
|-----|-------------------|-----------|
| `bsa53` | 71,999,995,678,620 | TỔNG TÀI SẢN |
| `bsa54` | 36,272,455,573,820 | TỔNG NỢ PHẢI TRẢ |
| `bsa78` | 35,727,540,104,800 | VỐN CHỦ SỞ HỮU |
| `bsa96` | 71,999,995,678,620 | NỢ PT + VỐN CSH |

---

## 3. Lỗi Mapping TRƯỚC V5

- **File lỗi**: `Version_2/golden_schema.json`
- **Triệu chứng**: Toàn bộ 188 field `CDKT`, `KQKD`, `LCTT` (normal company) có `vietcap_key: ""`.
- **Chỉ 10 field** được hardcode override trong `providers/vietcap.py` — nhưng **6/10 override cũng SAI**:
  - `cdkt_tong_cong_tai_san → bsa96` ❌ (đúng là `bsa53`)
  - `cdkt_no_phai_tra → bsa54` ✅ (trùng hợp đúng)
  - `cdkt_von_chu_so_huu → bsa79` ❌ (đúng là `bsa78`)
- **Hậu quả**: Fallback `f"bsa{sheet_row_idx}"` tạo mapping sequential (field[i]→bsa[i+1]) — SAI vì schema order ≠ API order.

## 4. Kết quả SAU V5 Fix

### Schema Coverage (Post-rebuild):
| Sheet | Total | Mapped | Empty | Coverage |
|-------|-------|--------|-------|----------|
| CDKT | 122 | 109 | 13 | 89.3% |
| KQKD | 25 | 25 | 0 | 100% |
| LCTT | 41 | 41 | 0 | 100% |
| CDKT_BANK | 87 | 87 | 0 | 100% |
| KQKD_BANK | 26 | 26 | 0 | 100% |
| LCTT_BANK | 52 | 52 | 0 | 100% |
| CDKT_SEC | 208 | 208 | 0 | 100% |
| KQKD_SEC | 80 | 80 | 0 | 100% |
| LCTT_SEC | 148 | 148 | 0 | 100% |
| NOTE | 157 | 0 | 157 | 0% (API không hỗ trợ) |

> 13 CDKT fields empty vì schema có nhiều dòng chi tiết hơn Vietcap (65 fields Assets vs 52 API keys).

### Accounting Identity (FPT 2024):
```
✅ Tổng Tài Sản    = 71,999,995,678,620 VND
✅ Nợ Phải Trả     = 36,272,455,573,820 VND  
✅ Vốn CSH         = 35,727,540,104,800 VND
✅ Nợ + Vốn        = 71,999,995,678,620 VND  ← KHỚP CHÍNH XÁC
✅ Tổng Nguồn Vốn  = 71,999,995,678,620 VND  ← KHỚP CHÍNH XÁC
```

## 5. Bank/Sec sheets (CDKT_BANK, KQKD_SEC...)

- Các sheet ngành **có `vietcap_key` đúng 100%** (đã được populate trước V5).
- Bank schema được dùng làm **Ground Truth** để xác nhận anchor points cho normal company.
- Các bsa key xuất hiện trong cả Bank và Normal schema đều dùng CÙNG key number.

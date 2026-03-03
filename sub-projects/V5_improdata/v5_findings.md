# 🔎 V5 Data Findings Log

Nơi ghi chú nhanh các phát hiện về cấu trúc dữ liệu, lỗi mapping, và thông tin API trong khuôn khổ dự án V5.

## 1. Hệ thống Key Prefix của Vietcap API

Vietcap API sử dụng **multi-prefix key system**. Mỗi section có nhiều prefix khác nhau:

### Balance Sheet (BALANCE_SHEET)
| Prefix | Ý nghĩa | Range | Áp dụng cho |
|--------|---------|-------|-------------|
| `bsa`  | Assets | 1-96 | Tất cả sector |
| `bsb`  | Liabilities + Equity | 97-179 | Tất cả sector |
| `bss`  | Securities sector | 133-257 | Chỉ CTCK |
| `bsi`  | Insurance sector | 139-287 | Chỉ Bảo hiểm |

### Income Statement (INCOME_STATEMENT)
| Prefix | Ý nghĩa | Áp dụng cho |
|--------|---------|-------------|
| `isa`  | Revenue/Profit general | Tất cả |
| `isb`  | Bank-specific IS items | Ngân hàng |
| `iss`  | Securities-specific | CTCK |

### Cash Flow (CASH_FLOW)
| Prefix | Ý nghĩa | Áp dụng cho |
|--------|---------|-------------|
| `cfa`  | General CF items | Tất cả |
| `cfb`  | Bank CF items | Ngân hàng |
| `cfs`  | Securities CF items | CTCK |

## 2. Lỗi Mapping hiện tại

- **File lỗi**: `Version_2/golden_schema.json`
- **Triệu chứng**: Toàn bộ ~400 field `CDKT`, `KQKD`, `LCTT` (normal company) có `vietcap_key: ""`.
- **Chỉ 10 field** được hardcode override trong `providers/vietcap.py` (dòng 45-55).
- **Hậu quả**: Fallback logic dùng `bsa{N}` cho tất cả row → row 97+ (Nợ PT, Vốn CSH) đọc sai key.

## 3. Dữ liệu sai mẫu (FPT 2024 – Balance Sheet)

| Row | Field | Giá trị Supabase | Đúng/Sai |
|-----|-------|------------------|----------|
| 23  | Thuế GTGT được khấu trừ | 26,464 tỷ | ❌ SAI (bằng Tổng TS dài hạn) |
| 27  | TÀI SẢN DÀI HẠN | 26,464 tỷ | ✅ Đúng |
| 38  | Nguyên giá TSCĐ hữu hình | -1,616 tỷ | ❌ SAI (nguyên giá phải dương) |

→ **Kết luận**: Key mapping bị lệch vài vị trí → giá trị hoán đổi giữa các dòng.

## 4. Bank/Sec sheets (CDKT_BANK, KQKD_SEC...)

- Các sheet ngành **có `vietcap_key` đúng** (đã được populate trước đó).
- Vấn đề chủ yếu nằm ở **standard sheets** (CDKT, KQKD, LCTT) cho **normal companies**.

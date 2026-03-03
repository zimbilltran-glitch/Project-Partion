# 🚧 V5 Challenges & Issues Log

Theo dõi các khó khăn kỹ thuật và hướng giải quyết trong quá trình làm V5, để agent đi sau nắm bắt tình hình.

## 1. Auto-Discovery Key Mapping

- **Tình trạng**: Pending
- **Chẩn đoán**: Cần match ~96 field_id trong schema với ~96 non-null keys trong raw API. Không có metadata label trong API response (chỉ có `bsa1: <value>`). Phải dựa vào **thứ tự row** và **giá trị** để cross-reference.
- **Giải pháp**: 
  1. Lấy tất cả non-null keys từ raw API response (đã có từ `_raw_fpt_bs.json`)
  2. Sắp xếp theo số thứ tự trong key name (bsa1, bsa2, ..., bsb97, ...)
  3. Map tuần tự vào `golden_schema.json` theo `row_number`
  4. Verify bằng cách so sánh giá trị API vs giá trị kỳ vọng từ Vietcap web

## 2. Xử lý key không liên tục (gaps)

- **Tình trạng**: Pending
- **Chẩn đoán**: API có thể trả về `bsa1, bsa2, ..., bsa22, bsa23` rồi nhảy sang `bsa27` (bỏ 24-26). Các key bị skip tương ứng với field không áp dụng cho một số công ty.
- **Giải pháp**: Script rebuild cần xử lý gaps bằng cách match theo **tổng số non-null keys** thay vì theo **số thứ tự key**.

## 3. Terminal encoding (Windows cp1252)

- **Tình trạng**: Biết rõ
- **Chẩn đoán**: PowerShell mặc định dùng cp1252, không hiển thị được tiếng Việt Unicode.
- **Giải pháp**: Tất cả Python output phải write to file (`encoding='utf-8'`), không `print()` trực tiếp.

## 4. Vietcap API Rate Limiting

- **Tình trạng**: Noted
- **Chẩn đoán**: API công khai, không cần auth, nhưng có thể giới hạn request nếu fetch quá nhiều ticker liên tục.
- **Giải pháp**: Thêm `time.sleep(1)` giữa mỗi ticker khi chạy batch VN30.

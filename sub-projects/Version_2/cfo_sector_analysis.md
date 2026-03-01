# Phân tích Đặc điểm Đầu mục Báo cáo Tài chính theo Nhóm Ngành

Dưới đây là kết quả phân tích sự khác biệt về cấu trúc Báo cáo Tài chính của 3 nhóm ngành tiêu biểu trong VN30.

## 1. Bản chất chung của 3 Nhóm Ngành
Báo cáo tài chính chuẩn mực (VAS) được Bộ Tài chính quy định có sự khác biệt rõ rệt giữa doanh nghiệp Dịch vụ/Sản xuất (Phi tài chính), Ngân hàng và Chứng khoán.

- **Ngành Phi Tài chính (HPG, VIC, VNM...)**: Chuẩn mực chung (Thông tư 200). Các khoản mục thiên về tài sản vật chất (TSCĐ, Tồn kho) và vòng quay vốn lưu động (Phải thu, Phải trả).
- **Ngành Ngân hàng (MBB, VCB, CTG...)**: Đặc thù luân chuyển vốn. Tiền không chỉ là công cụ thanh toán mà là "hàng hóa". Không có khái niệm "Hàng tồn kho" hay "Phải thu người mua" theo nghĩa đen.
- **Ngành Chứng khoán (SSI, VND...)**: Đặc thù đầu tư tài sản tài chính (FVTPL, HTM, AFS) và môi giới.

## 2. Các điểm khác biệt cốt lõi gây ra lỗi hiển thị (Trống dữ liệu)

Vấn đề trên hệ thống Finsang hiện tại xuất phát từ việc luồng xử lý `Version_2/pipeline.py` đang dùng một `golden_schema.json` duy nhất (dựa trên nhóm Phi tài chính) để áp đặt cho tất cả mã.

### A. Ngân hàng (Ví dụ: MBB) không có các đầu mục sau:
1. **cdkt_hang_ton_kho_rong (Hàng tồn kho)**: Ngân hàng không sản xuất hay bán lẻ hàng hóa, nên mục này hoàn toàn rỗng `0.0` (Nan).
2. **cdkt_phai_tra_nguoi_ban / cdkt_nguoi_mua_tra_tien_truoc**: Ngân hàng có "Tiền gửi của khách hàng" hoặc "Phát hành giấy tờ có giá", chứ không có Phải trả người bán thông thường.
3. **cdkt_von_gop**: Ngân hàng gọi là "Vốn điều lệ của tổ chức tín dụng". Việc map sang `cdkt_von_gop` bị thất bại, dẫn tới chỉ số "Vốn góp" rỗng.
4. **cdkt_lai_chua_phan_phoi / cdkt_tong_cong_nguon_von**: Ngân hàng có các quỹ dự trữ riêng (Quỹ dự trữ bổ sung VĐL, Quỹ dự phòng tài chính), cách tổng hợp khác với doanh nghiệp thường. Trong Database, Vietcap trả về các mã như `cdkt_von_chu_so_huu` thay vì `cdkt_von_gop`.

### B. Công ty Chứng khoán (Ví dụ: SSI) khác biệt ở cấu trúc nguồn vốn:
1. Nền tảng tài sản của SSI chủ yếu là **FVTPL** (Tài sản ghi nhận thông qua Lãi/Lỗ), **HTM** (Giữ đến ngày đáo hạn) và **Các khoản cho vay Margin**.
2. Khi giao diện dùng chuẩn Phi tài chính để tìm "Tài sản cố định" hay "Đầu tư ngắn hạn", SSI sẽ không fit đúng, gây ra các hàng trống.
3. Trong kết quả kinh doanh, SSI không có "Giá vốn hàng bán" mà là "Chi phí hoạt động kinh doanh chứng khoán". Dẫn đến việc không thể tự động tính "Lợi nhuận gộp" theo cách thông thường.

## 3. Tại sao giao diện MBB trống nhiều dòng?
Logic hiện tại trong `metrics.py` đang tìm kiếm theo `field_id` của ngành Sản xuất:
- Cố tìm `cdkt_hang_ton_kho_rong` -> Đối với MBB là 0.
- Cố tìm `cdkt_vay_ngan_han` -> Có khoản "Tiền gửi của khách hàng" khổng lồ nhưng không được tính vào vay ngắn hạn thông thường.
- Điểm chết: Giao diện hiển thị `-` cho các khoản không áp dụng cho Ngân hàng, làm UI có vẻ trống rỗng, dù Ngân hàng có tài sản rất lớn. Ban nãy tôi đã xử lý fix kỹ thuật biến các mục rỗng thực sự thành "khoảng trắng" để bớt rác UI, nhưng bản chất vẫn là dùng "Khung xương của ngành Thép để đo cho ngành Bank".

## 4. Đề xuất khắc phục (Tầm nhìn CFO)
Để giao diện Finsang Terminal "chuẩn ngành" và không bị rỗng dọc rỗng ngang:
1. Sẽ cần tạo ra **3 Golden Schemas** khác biệt trong Backend: `schema_normal.json`, `schema_bank.json`, `schema_sec.json`.
2. Khi người dùng chọn mã (VD: MBB -> Bank), Data Pipeline sẽ phân loại (Sector Routing) và UI tự động load bộ chỉ số dành riêng cho Ngân hàng (nhấn mạnh vào NIM, LDR, Tiền gửi, CASA rỗng).
3. Tương tự với SSI -> Load bộ chỉ số Chứng khoán (Margin, FVTPL móng).

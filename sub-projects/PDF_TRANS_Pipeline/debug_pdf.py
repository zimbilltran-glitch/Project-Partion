"""Debug: In 500 ký tự đầu tiên từ từng trang của NLG Q4 PDF để hiểu cấu trúc thực"""
import fitz, os

PDF_PATH = os.path.join(os.path.dirname(__file__), 'pdfs', 'NLG', 'NLG_Q4_2024.pdf')
doc = fitz.open(PDF_PATH)
print(f"Total pages: {len(doc)}")
print(f"PDF metadata: {doc.metadata}")
print()

for page_num in range(min(len(doc), 80)):
    page = doc[page_num]
    text = page.get_text("text").strip()
    if text:
        # Tìm trang chứa bảng tài chính chính
        text_lower = text.lower()
        if any(kw in text_lower for kw in [
            "doanh thu", "lợi nhuận", "kết quả", "tài sản", 
            "lưu chuyển", "nguồn vốn", "cân đối"
        ]):
            print(f"\n--- PAGE {page_num+1} ---")
            print(text[:2000])
            print("...")

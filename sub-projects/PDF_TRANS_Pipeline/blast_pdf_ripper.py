import os
import json
try:
    import fitz  # PyMuPDF
    from thefuzz import fuzz, process
except ImportError:
    print("Warning: Missing packages. Please install PyMuPDF and thefuzz (pip install PyMuPDF thefuzz)")
    fitz, fuzz, process = None, None, None

def is_fuzzy_match(text, keywords, threshold=85):
    """
    So khớp mờ chuỗi văn bản với danh sách các từ khoá mục tiêu.
    Ví dụ: "K Ế T  Q U Ả  K I N H  D O A N H" có thể khớp với "Kết quả kinh doanh".
    """
    if not fuzz or not text:
        return False
        
    # Làm sạch chuỗi trước khi so sánh
    cleaned_str = " ".join(text.split()).upper()
    best_match, score = process.extractOne(cleaned_str, [kw.upper() for kw in keywords])
    return score >= threshold

def extract_financial_tables_from_pdf(pdf_path: str):
    """
    Trích xuất bảng "Kết quả kinh doanh", "Cân đối kế toán" từ file PDF report.
    Có áp dụng Fuzzy Matching để trị các font chữ hay bị dãn cách (K É T  Q U Ả).
    """
    if not fitz:
        return {"error": "Missing PyMuPDF package"}
        
    extracted_data = {}
    
    target_keywords = [
        "KẾT QUẢ KINH DOANH",
        "KẾT QUẢ HOẠT ĐỘNG KINH DOANH",
        "LƯU CHUYỂN TIỀN TỆ",
        "BẢNG CÂN ĐỐI KẾ TOÁN"
    ]
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"error": f"Failed to open PDF: {e}"}

    for page_num, page in enumerate(doc):
        # Lấy toàn bộ text trên trang ở dạng dictionary để phân tích bounding box
        text_blocks = page.get_text("blocks")
        
        # Tạo cờ (flag) xem trang này có chứa bảng mục tiêu hay không
        found_table = None
        for block in text_blocks:
            # block[4] là đoạn text
            block_text = block[4].replace("\n", " ").strip()
            
            # Quét Fuzzy Scan
            if is_fuzzy_match(block_text, target_keywords):
                found_table = block_text
                break
                
        if found_table:
            print(f"[{os.path.basename(pdf_path)}] Found table target on Page {page_num + 1} (~ {found_table})")
            # Ở bản MVP thực tế, chúng ta sẽ gọi page.find_tables() để crop dữ liệu chính xác
            # PyMuPDF có hàm page.find_tables() mạnh mẽ để trích xuất dưới dạng List các dòng/cột.
            tables = page.find_tables()
            for i, table in enumerate(tables):
                extracted_data[f"page_{page_num}_table_{i}"] = table.extract()
    
    doc.close()
    return extracted_data

def fallback_ocr(pdf_path: str):
    """
    Fallback mechanisms cho bản BCTC scan bằng mộc đỏ (Không có text ẩn bên trong PDF).
    Sử dụng pytesseract / tesseract-ocr
    """
    print(f"[{os.path.basename(pdf_path)}] Empty Text Detected. Triggering Fallback OCR Engine...")
    # Placeholder cho tiến trình OCR
    return {"status": "pending_ocr"}

if __name__ == "__main__":
    # Test Module
    sample_pdf = os.path.join(os.path.dirname(__file__), 'sample.pdf')
    if os.path.exists(sample_pdf):
        print(json.dumps(extract_financial_tables_from_pdf(sample_pdf), ensure_ascii=False, indent=4))
    else:
        print("Please provide a sample PDF to test extraction.")

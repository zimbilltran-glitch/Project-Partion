"""Debug: Kiểm tra TẤT CẢ 4 PDFs xem file nào có text layer vs scanned image"""
import fitz, os

PDF_DIR = os.path.join(os.path.dirname(__file__), 'pdfs', 'NLG')

for fname in sorted(os.listdir(PDF_DIR)):
    if not fname.endswith('.pdf'):
        continue
    pdf_path = os.path.join(PDF_DIR, fname)
    doc = fitz.open(pdf_path)
    meta = doc.metadata
    
    # Kiểm tra text layer trên 5 trang đầu
    total_chars = 0
    sample_text = ""
    for i in range(min(5, len(doc))):
        t = doc[i].get_text("text")
        total_chars += len(t)
        if not sample_text and t.strip():
            sample_text = t[:300]

    creator = meta.get('creator', '')
    producer = meta.get('producer', '')
    pdf_type = "✅ DIGITAL (text)" if total_chars > 100 else "❌ SCANNED (image only)"
    
    print(f"\n{'='*60}")
    print(f"File   : {fname}")
    print(f"Creator: {creator}")
    print(f"Type   : {pdf_type} ({total_chars} chars in first 5 pages)")
    if sample_text:
        print(f"Sample : {sample_text[:200]}")
    doc.close()

"""
PDF_TRANS Extraction Test: FPT Digital PDFs from HSX
Real test: Digital PDF (with text layer) → PyMuPDF → Long Format Table
"""
import os, sys, re, json, requests

BASE_DIR = os.path.dirname(__file__)
PDF_DIR = os.path.join(BASE_DIR, 'pdfs', 'FPT')
os.makedirs(PDF_DIR, exist_ok=True)

HSX_PDFS = [
    {
        "quarter": "2024-Q4",
        "url": "https://staticfile.hsx.vn/Uploads/FinancialReport/13/20250124_20250124%20-%20FPT%20-%20BCTC%20hop%20nhat%20Quy%204%20nam%202024.pdf",
        "filename": "FPT_Q4_2024.pdf"
    },
    {
        "quarter": "2024-Q3",
        "url": "https://staticfile.hsx.vn/Uploads/FinancialReport/13/20241024_20241023%20-%20FPT%20-%20BCTC%20hop%20nhat%20Quy%203%20nam%202024.pdf",
        "filename": "FPT_Q3_2024.pdf"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.hsx.vn/"
}

# Keyword pattern cho các phần BCTC
SECTION_KEYWORDS = {
    "KQKD": ["kết quả hoạt động kinh doanh", "kết quả kinh doanh", "báo cáo kết quả"],
    "CDKT": ["bảng cân đối kế toán", "cân đối kế toán"],
    "LCTT": ["báo cáo lưu chuyển tiền tệ", "lưu chuyển tiền tệ"]
}

def download_pdfs():
    print("=== STEP 1: Downloading FPT PDFs from HSX ===")
    for item in HSX_PDFS:
        dest = os.path.join(PDF_DIR, item['filename'])
        if os.path.exists(dest):
            print(f"  [SKIP] {item['filename']} already exists")
            continue
        print(f"  Downloading {item['quarter']}...")
        r = requests.get(item['url'], headers=HEADERS, timeout=30, stream=True)
        if r.status_code == 200:
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            print(f"  ✅ {item['filename']} ({os.path.getsize(dest)//1024} KB)")
        else:
            print(f"  ❌ HTTP {r.status_code}")

def extract_section_tables(pdf_path, quarter):
    """Extract KQKD / CDKT / LCTT tables from digital PDF"""
    try:
        import fitz
    except ImportError:
        print("pip install PyMuPDF"); return {}

    doc = fitz.open(pdf_path)
    print(f"\n  [{quarter}] {len(doc)} pages, Creator: {doc.metadata.get('creator','')}")
    
    # Gom toàn bộ text theo trang
    pages_text = [(i, doc[i].get_text("text")) for i in range(len(doc))]
    total_chars = sum(len(t) for _, t in pages_text)
    print(f"  Total text chars: {total_chars:,}")

    # Tìm trang bắt đầu của từng section
    section_pages = {}
    for section, keywords in SECTION_KEYWORDS.items():
        for page_num, text in pages_text:
            if any(kw in text.lower() for kw in keywords):
                if section not in section_pages:
                    section_pages[section] = page_num
                    print(f"  Found {section} on page {page_num + 1}")

    # Trích xuất lines từ mỗi section (tối đa 6 trang liên tiếp)
    extracted = {}
    for section, start_page in section_pages.items():
        all_lines = []
        for pn in range(start_page, min(start_page + 6, len(pages_text))):
            page_text = pages_text[pn][1]
            all_lines.extend([l.strip() for l in page_text.split('\n') if l.strip()])
        extracted[section] = all_lines

    doc.close()
    return extracted

def parse_rows(lines):
    """Trích xuất dòng có số liệu kế toán từ list of lines"""
    rows = []
    # Pattern: tên khoản mục + số tiền (VD: "Doanh thu thuần  1,234,567")
    num_re = re.compile(r'[\d]{1,3}(?:[,\.]\d{3})+')
    
    current_item = ""
    for line in lines:
        nums = num_re.findall(line)
        if nums:
            # Lấy phần text trước số đầu
            pos = num_re.search(line).start()
            item_text = line[:pos].strip().rstrip('. \t')
            if not item_text and current_item:
                item_text = current_item
            if item_text and len(item_text) > 2:
                # Chuyển sang Tỷ VND (giả định đơn vị là triệu)
                parsed_nums = []
                for n in nums[:4]:  # max 4 cột (4 quý)
                    try:
                        parsed_nums.append(float(n.replace(',', '').replace('.', '')))
                    except:
                        pass
                if parsed_nums:
                    rows.append({"item": item_text, "values": parsed_nums})
                    current_item = ""
        elif len(line) > 5 and not any(c.isdigit() for c in line):
            current_item = line
    return rows

def main():
    download_pdfs()

    print("\n=== STEP 2: Extracting Financial Tables ===")
    all_results = {}
    for item in HSX_PDFS:
        path = os.path.join(PDF_DIR, item['filename'])
        if not os.path.exists(path):
            continue
        raw = extract_section_tables(path, item['quarter'])
        q_data = {}
        for section, lines in raw.items():
            rows = parse_rows(lines)
            q_data[section] = rows
            print(f"  [{item['quarter']}] {section}: {len(rows)} rows")
        all_results[item['quarter']] = q_data

    # Preview KQKD
    print("\n=== STEP 3: KQKD Preview (FPT from HSX PDF) ===")
    for quarter, sections in all_results.items():
        if "KQKD" not in sections:
            continue
        print(f"\n  ── {quarter} ──")
        print(f"  {'KHOẢN MỤC':<55} {'GIÁ TRỊ (triệu VND)':>25}")
        print("  " + "─" * 82)
        for row in sections["KQKD"][:20]:
            vals = " | ".join(f"{int(v):>15,}" for v in row['values'][:2])
            print(f"  {row['item'][:54]:<55} {vals}")

    # Lưu kết quả
    out = os.path.join(BASE_DIR, '.tmp', 'fpt_pdf_extracted.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved to: {out}")

if __name__ == "__main__":
    main()

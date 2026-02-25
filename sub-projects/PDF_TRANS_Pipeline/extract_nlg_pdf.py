"""
PDF_TRANS Core Test: Download & Extract NLG BCTC PDFs from HSX
Đây là luồng đúng: PDF gốc từ HSX → PyMuPDF → Long Format Table
"""
import os, sys, json, requests, re
import urllib.request

BASE_DIR = os.path.dirname(__file__)
PDF_DIR = os.path.join(BASE_DIR, 'pdfs', 'NLG')
os.makedirs(PDF_DIR, exist_ok=True)

# ─── Danh sách PDF thực tế từ HSX ─────────────────────────────────────────────
HSX_PDFS = [
    {
        "quarter": "2024-Q4",
        "url": "https://staticfile.hsx.vn/Uploads/FinancialReport/336/20250124_20250123%20-%20NLG%20-%20CBTT%20Bao%20cao%20tai%20chinh%20quy%204%20nam%202024%20-%20Hop%20nhat.pdf",
        "filename": "NLG_Q4_2024.pdf"
    },
    {
        "quarter": "2024-Q3",
        "url": "https://staticfile.hsx.vn/Uploads/FinancialReport/336/20241021_20241021%20-%20NLG%20-%20BCTC%20hop%20nhat%20Quy%203%202024.pdf",
        "filename": "NLG_Q3_2024.pdf"
    },
    {
        "quarter": "2024-Q2",
        "url": "https://staticfile.hsx.vn/Uploads/FinancialReport/336/20240724_20240724%20-%20NLG%20-%20CBTT%20Bao%20cao%20tai%20chinh%20quy%202%20nam%202024%20-%20Hop%20nhat.pdf",
        "filename": "NLG_Q2_2024.pdf"
    },
    {
        "quarter": "2024-Q1",
        "url": "https://staticfile.hsx.vn/Uploads/FinancialReport/336/20240426_20240426%20-%20NLG%20-%20Bao%20cao%20tai%20chinh%20quy%201%20nam%202024%20-%20Hop%20nhat%20(kem%20GT).pdf",
        "filename": "NLG_Q1_2024.pdf"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.hsx.vn/"
}

# ─── Step 1: Tải PDFs ──────────────────────────────────────────────────────────
def download_pdfs():
    print("\n=== STEP 1: Downloading PDFs from HSX ===")
    for item in HSX_PDFS:
        dest = os.path.join(PDF_DIR, item['filename'])
        if os.path.exists(dest):
            print(f"  [SKIP] Already exists: {item['filename']}")
            continue
        print(f"  Downloading {item['quarter']} → {item['filename']}...")
        try:
            r = requests.get(item['url'], headers=HEADERS, timeout=30, stream=True)
            if r.status_code == 200:
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                size_kb = os.path.getsize(dest) / 1024
                print(f"  ✅ {item['filename']} ({size_kb:.0f} KB)")
            else:
                print(f"  ❌ HTTP {r.status_code} for {item['quarter']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

# ─── Step 2: Extract Tables từ PDF ────────────────────────────────────────────
def extract_pdf(pdf_path, quarter):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Missing PyMuPDF. pip install PyMuPDF")
        return {}

    # Keyword targets (Vietnamese accounting section headers)
    SECTION_KEYWORDS = {
        "KQKD": ["kết quả hoạt động kinh doanh", "kết quả kinh doanh", "kqkd"],
        "CDKT": ["bảng cân đối kế toán", "cân đối kế toán", "cdkt"],
        "LCTT": ["lưu chuyển tiền tệ", "lưu chuyển tiền", "lctt"]
    }

    doc = fitz.open(pdf_path)
    all_text_pages = []
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        all_text_pages.append((page_num, text))

    # Tìm trang chứa từng bảng
    sections_found = {}
    for page_num, text in all_text_pages:
        text_lower = text.lower()
        for section, keywords in SECTION_KEYWORDS.items():
            if section not in sections_found:
                if any(kw in text_lower for kw in keywords):
                    sections_found[section] = page_num
                    print(f"  [{quarter}] Found {section} on page {page_num + 1}")

    # Extract raw lines từ các trang mục tiêu
    extracted = {}
    for section, start_page in sections_found.items():
        lines = []
        # Quét tối đa 5 trang sau trang tìm thấy
        for page_num in range(start_page, min(start_page + 5, len(all_text_pages))):
            page_text = all_text_pages[page_num][1]
            for line in page_text.split('\n'):
                line = line.strip()
                if line:
                    lines.append(line)
        extracted[section] = lines

    doc.close()
    return extracted

def find_numeric_rows(lines):
    """Lọc ra các dòng có chứa số liệu kế toán (số nguyên lớn)"""
    data_rows = []
    number_pattern = re.compile(r'[\d,\.\s]+')
    
    for line in lines:
        # Tìm dòng có tên khoản mục lẫn số
        nums = re.findall(r'\b\d[\d,\.]{3,}\b', line)
        if nums:
            # Làm sạch tên khoản mục (phần trước số đầu tiên)
            first_num_pos = re.search(r'\b\d[\d,\.]{3,}\b', line)
            if first_num_pos:
                item_name = line[:first_num_pos.start()].strip().rstrip('.')
                values = [v.replace(',', '') for v in nums]
                if item_name and len(item_name) > 3:
                    data_rows.append({
                        "item": item_name,
                        "values_raw": nums,
                        "values_numeric": [float(v) for v in values if v]
                    })
    return data_rows

# ─── Step 3: In kết quả ────────────────────────────────────────────────────────
def main():
    # 1. Tải PDF
    download_pdfs()

    print("\n=== STEP 2: Extracting Tables from PDFs ===")
    all_results = {}

    for item in HSX_PDFS:
        pdf_path = os.path.join(PDF_DIR, item['filename'])
        if not os.path.exists(pdf_path):
            print(f"  ❌ Missing: {item['filename']}")
            continue

        print(f"\n  Processing {item['quarter']} ({item['filename']})...")
        raw_sections = extract_pdf(pdf_path, item['quarter'])
        
        quarter_data = {}
        for section, lines in raw_sections.items():
            rows = find_numeric_rows(lines)
            quarter_data[section] = rows
            print(f"    {section}: {len(rows)} numeric rows found")

        all_results[item['quarter']] = quarter_data

    # In KQKD preview
    print("\n\n=== STEP 3: KQKD Preview (NLG 4 Quarters from PDF) ===")
    print(f"{'KHOẢN MỤC':<55} {'Q1/2024':>15} {'Q2/2024':>15} {'Q3/2024':>15} {'Q4/2024':>15}")
    print("─" * 70)

    # Lấy danh sách dòng từ Q4 làm template
    template_items = []
    if "2024-Q4" in all_results and "KQKD" in all_results["2024-Q4"]:
        template_items = [r['item'] for r in all_results["2024-Q4"]["KQKD"]]

    for item_name in template_items[:25]:
        row_vals = []
        for q in ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]:
            val_str = "—"
            if q in all_results and "KQKD" in all_results[q]:
                match = next((r for r in all_results[q]["KQKD"] if r['item'] == item_name), None)
                if match and match['values_numeric']:
                    # Lấy giá trị đầu tiên (đơn vị: triệu VND → quy đổi sang Tỷ)
                    raw_val = match['values_numeric'][0]
                    val_str = f"{raw_val/1_000:,.1f}"  # Giả sử đơn vị triệu → Tỷ
            row_vals.append(val_str)
        print(f"{item_name[:54]:<55} {row_vals[0]:>15} {row_vals[1]:>15} {row_vals[2]:>15} {row_vals[3]:>15}")

    # Lưu JSON output
    out_file = os.path.join(BASE_DIR, '.tmp', 'nlg_pdf_extracted.json')
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Raw extraction saved to: {out_file}")

if __name__ == "__main__":
    main()

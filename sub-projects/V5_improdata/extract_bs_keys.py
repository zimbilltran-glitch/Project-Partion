import json

fpt_bs = {
    "TỔNG TÀI SẢN": 71999995678630,
    "TÀI SẢN NGẮN HẠN": 45535942846453,
    "Tiền và tương đương tiền": 9115440466664,
    "Tiền": 6725619929988,
    "Đầu tư ngắn hạn": 21785213686866,
    "TÀI SẢN DÀI HẠN": 26464052832167,
    "NỢ PHẢI TRẢ": 34103165778753,
    "Vay ngắn hạn": 14446430335041,
    "VỐN CHỦ SỞ HỮU": 37896829899877,
    "Lợi ích Cổ đông thiểu số":  71999995678630 - 34103165778753 - 37896829899877 # just a check, wait FPT has "Vốn và các quỹ: 37896...
}
fpt_bs["Lợi ích Cổ đông thiểu số"] = 5932309621604 # at the bottom of the image for FPT 2024

mbb_bs = {
    "TỔNG TÀI SẢN": 1128801062000000,
    "Tiền mặt": 3349165000000,
    "Cho vay khách hàng": 1011741481000000,
    "Dự phòng rủi ro cho vay khách hàng": -11608861000000,
    "TỔNG NỢ PHẢI TRẢ": 1011741481000000, # wait total liabilities is the same? No, NỢ PHẢI TRẢ is 1,011,741... wait. I see "Các khoản nợ Chính phủ... 8,156,285..." Let's check "Tiền gửi của khách hàng"
    "Tiền gửi của khách hàng": 714154479000000,
    "VỐN CHỦ SỞ HỮU": 1170595810000000,
    "Lợi ích của cổ đông thiểu số": 4910880000000
}

vci_bs = {
    "TỔNG TÀI SẢN": 25601365061689,
    "TÀI SẢN NGẮN HẠN": 25487461862641,
    "FVTPL": 10256666862111,
    "Các khoản cho vay": 12393126825910,
    "NỢ PHẢI TRẢ": 15459620019252,
    "Vay ngắn hạn": 14076821433520,
    "VỐN CHỦ SỞ HỮU": 10141745042437
}

def find_in_json(filepath, targets, year):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    mapping = {}
    for period in data.get("data", {}).get("years", []):
        if period.get("yearReport") == year:
            for name, val in targets.items():
                found = False
                for k, v in period.items():
                    if isinstance(v, (int, float)) and abs(v - val) < 1000:
                        mapping[name] = k
                        found = True
                        break
                if not found:
                    mapping[name] = "NOT_FOUND"
                    
    for k, v in mapping.items():
        print(f"{v}: {k}")

print("--- FPT 2024 (bsa) ---")
find_in_json("_raw_fpt_bs.json", fpt_bs, 2024)

print("\n--- MBB 2024 (bsb) ---")
find_in_json("_raw_mbb_bs.json", mbb_bs, 2024)

print("\n--- VCI 2024 (bss) ---")
find_in_json("_raw_vci_bs.json", vci_bs, 2024)


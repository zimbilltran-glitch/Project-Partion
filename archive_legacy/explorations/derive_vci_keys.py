import json

vci_ground_truth_2024 = {
    "Doanh thu HĐ": 3594400689179,
    "FVTPL (Thu)": 1778614820544,
    "Lãi bán FVTPL": 1759391703072, # From earlier probe
    "Chênh lệch tăng đánh giá lại FVTPL": 19223117472, # 1778614820544 - 1759391703072
    "AFS (Thu)": 228883677917,
    "Lãi cho vay": 677054693998,
    "Doanh thu Môi giới": 729603724265,
    "Bảo lãnh": 48153605679,
    "Tư vấn ĐTCK": 25662817734,
    "Lưu ký CK": 16505798074,
    "Tư vấn TC": -19181019003,
    "Khác (Thu)": 50050490404,
    "Chi phí HĐ": -1257511855394,
    "FVTPL (Chi)": -446145038705,
    "Môi giới (Chi)": -208851457193,
    "Chi phí QLDN": -221684213858,
    "Doanh thu HĐTC": 13006242126,
    "Lợi nhuận Kế toán trước thuế": 1128527249634,
    "Lợi nhuận Kế toán sau thuế": 910692113293
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

print("VCI 2024 keys mapping:")
find_in_json("_raw_vci_is.json", vci_ground_truth_2024, 2024)

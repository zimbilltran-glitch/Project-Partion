import json

fpt_ground_truth_2024 = {
    "Doanh thu bán hàng và cung cấp dịch vụ": 62962652134635,
    "Các khoản giảm trừ": -113857783268,
    "Doanh thu thuần": 62848794351367,
    "Giá vốn hàng bán": -39150445981451,
    "Lợi nhuận gộp": 23698348369916,
    "Doanh thu HĐ tài chính": 1935749115305,
    "Chi phí TC": -1811547381981,
    "Chi phí lãi vay": -551639361786,
    "Lãi lỗ công ty liên doanh liên kết": 392531256272,
    "Chi phí bán hàng": -6115961971783,
    "Chi phí QLDN": -7074038614774,
    "Lợi nhuận hoạt động kinh doanh": 11025080772955,
    "Thu nhập khác, ròng": 44585644864,
    "Thu nhập khác": 175450599740,
    "Chi phí khác": -130864954876,
    "Lãi/lỗ trước thuế": 11069666417819,
    "Chi phí thuế TNDN": -1642243887375,
    "Thuế hiện hành": -1922927614658,
    "Thuế hoãn lại": 280683727283,
    "Lãi thuần sau thuế": 9427422530444,
    "Lợi ích CĐTS": 1570654718266,
    "Lợi nhuận Cổ đông Công ty mẹ": 7856767812178,
    "EPS": 4944
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

print("FPT 2024 keys mapping:")
import os 
if not os.path.exists('_raw_fpt_is.json'):
    import requests
    url = "https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/FPT/financial-statement?section=INCOME_STATEMENT"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://trading.vietcap.com.vn/", "Origin": "https://trading.vietcap.com.vn"}
    with open('_raw_fpt_is.json', 'w') as f:
        json.dump(requests.get(url, headers=headers).json(), f)

find_in_json("_raw_fpt_is.json", fpt_ground_truth_2024, 2024)

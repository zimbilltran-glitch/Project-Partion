import requests, re, json

url = "https://trading.vietcap.com.vn/"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
js_files = re.findall(r'src="(/_next/static/chunks/main-.*?.js)"', r.text)
if not js_files:
    js_files = re.findall(r'src="(/_next/static/chunks/[^"]+\.js)"', r.text)

print(f"Found {len(js_files)} JS chunk paths: {js_files[:5]}")

for js in js_files:
    if "pages/" in js or "app/" in js:
        full_url = f"https://trading.vietcap.com.vn{js}"
        res = requests.get(full_url, headers={"User-Agent": "Mozilla/5.0"})
        if "Tiền gửi tại Ngân hàng Nhà nước" in res.text:
            print(f"FOUND BANK SCHEMA in {js}")
            # Try to grab the array or object containing it
            with open(".tmp/vietcap_bank_script.js", "w", encoding="utf-8") as f:
                f.write(res.text)

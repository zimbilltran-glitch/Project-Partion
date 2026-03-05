import requests, json

headers = {"User-Agent": "Mozilla/5.0"}

def fetch_simplize_schema(ticker, output_file):
    # Simplize API endpoint for full financial statements
    url = f"https://api.simplize.vn/api/company/fi/statement/{ticker}?statementDate=2024-12-31&period=Y"
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code == 200:
        data = r.json()
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Dumped {ticker} schema to {output_file}")
    else:
        print(f"Failed to fetch {ticker}: {r.status_code}")

fetch_simplize_schema("MBB", ".tmp/simplize_mbb_schema.json")
fetch_simplize_schema("SSI", ".tmp/simplize_ssi_schema.json")
fetch_simplize_schema("HPG", ".tmp/simplize_hpg_schema.json")

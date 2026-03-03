import requests, json

def test_ssi():
    TICKER = "MBB"
    # SSI common public endpoint for indicators
    url = f"https://wgateway-iboard.ssi.com.vn/api/v1/FinancialIndicator/GetFinancialIndicator?symbol={TICKER}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://iboard.ssi.com.vn/",
    }
    
    print(f"  GET SSI Indicators ({TICKER})...", end=" ")
    try:
        r = requests.get(url, headers=HEADERS if 'HEADERS' in globals() else headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            print("200 OK")
            # Filter for CASA / NPL if possible
            # We don't know the exact structure, so we dump a few keys
            print(json.dumps(data.get('data', [])[:5], ensure_ascii=False, indent=2))
        else:
            print(f"ERROR {r.status_code}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_ssi()

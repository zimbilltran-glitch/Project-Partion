import urllib.request
import json
url = "https://finfo-api.vndirect.com.vn/v4/financialModels?q=displayType:1"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode())
        print(data)
except Exception as e:
    print(e)

"""
Probe vnstock company module for P/E, P/B, market cap, dividend yield
"""
import json
from vnstock import Vnstock

TICKER = "VHC"
s = Vnstock().stock(symbol=TICKER, source="VCI")
comp = s.company

print("=== company.overview ===")
try:
    ov = comp.overview()
    print(json.dumps(ov.to_dict(orient="records")[0] if hasattr(ov,"to_dict") else ov, indent=2, ensure_ascii=False, default=str))
except Exception as e:
    print(f"overview: {e}")

print("\n=== company.ratio_summary ===")
try:
    rs = comp.ratio_summary()
    print(json.dumps(rs.to_dict(orient="records")[:3] if hasattr(rs,"to_dict") else rs, indent=2, ensure_ascii=False, default=str))
except Exception as e:
    print(f"ratio_summary: {e}")

print("\n=== company.profile ===")
try:
    prof = comp.profile()
    if hasattr(prof, "to_dict"):
        d = prof.to_dict(orient="records")
        print(json.dumps(d[0] if d else {}, indent=2, ensure_ascii=False, default=str))
    else:
        print(json.dumps(prof, indent=2, ensure_ascii=False, default=str))
except Exception as e:
    print(f"profile: {e}")

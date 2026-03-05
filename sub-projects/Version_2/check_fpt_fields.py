import json
import codecs

with codecs.open("probe_FPT_BS.json", "r", "utf-8") as f:
    d = json.load(f)

items = d["quarters"][0]
with codecs.open("output_fpt.txt", "w", "utf-8") as out:
    for k, v in items.items():
        if k.startswith("bsa") and v:
            out.write(f"{k}: {v}\n")

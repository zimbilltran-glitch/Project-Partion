from pipeline import DATA_DIR
import pandas as pd
import json

fixes_normal = [
    'cdkt_dau_tu_ngan_han',
    'cdkt_cac_khoan_phai_thu',
    'cdkt_hang_ton_kho',
    'cdkt_tai_san_co_dinh',
    'cdkt_tai_san_do_dang_dai_han',
    'cdkt_phai_tra_nguoi_ban',
    'cdkt_nguoi_mua_tra_tien_truoc',
    'cdkt_vay_ngan_han',
    'cdkt_vay_dai_han',
    'cdkt_von_gop',
    'cdkt_loi_nhuan_sau_thue_chua_phan_phoi',
    'cdkt_co_phieu_quy'
]

from security import get_cipher
import io
import pyarrow.parquet as pq

cipher = get_cipher()

def load_pq(path):
    if cipher:
        with open(path, "rb") as f:
            encrypted_data = f.read()
        try:
            return pd.read_parquet(io.BytesIO(cipher.decrypt(encrypted_data)))
        except:
            return pd.read_parquet(path)
    return pd.read_parquet(path)

inserts = []
seen = set()
for pt in ['quarter', 'year']:
    df = load_pq(DATA_DIR / "FPT" / f"period_type={pt}" / "sheet=cdkt" / "FPT.parquet")
    sub = df[df['field_id'].isin(fixes_normal)]
    for _, row in sub.iterrows():
        if pd.isna(row['value']):
             continue
        key = (row['period_label'], row['field_id'])
        if key in seen:
            continue
        seen.add(key)
        name_esc = str(row['vn_name']).replace("'", "''")
        inserts.append(f"('FPT', '{row['period_label']}', '{row['field_id']}', '{name_esc}', {row['value']}, '{row['unit']}', {row['level']}, {row['sheet_row_idx']}, 'vietcap')")

with open("sync_fpt_bs.sql", "w", encoding="utf-8") as out:
    if inserts:
        out.write("INSERT INTO public.balance_sheet (stock_name, period, item_id, item, value, unit, levels, row_number, source) VALUES\n")
        out.write(",\n".join(inserts))
        out.write("\nON CONFLICT (stock_name, period, item_id, source) DO UPDATE SET value = EXCLUDED.value;\n")

print(f"Generated {len(inserts)} inserts")

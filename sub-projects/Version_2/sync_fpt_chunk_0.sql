DELETE FROM public.balance_sheet WHERE stock_name = 'FPT' AND item_id IN (
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
);
"""
Phase M — Metrics: Derived Ratios Engine
metrics.py — Calculates specialized dynamic financial ratios from Parquet sheets.
"""

import argparse
import pandas as pd
from pipeline import load_tab_from_supabase
from sector import get_sector

def calc_normal_metrics(periods, cdkt, kqkd, lctt, get_row, clean_num, add_row):
    """Bộ chỉ số dành cho Doanh nghiệp Phi tài chính (Sản xuất, Bán lẻ, BĐS...)"""
    
    # helper to sum multiple rows by nature
    def sum_nature(sheet, *fids):
        res = {}
        for p in periods:
            total = 0
            has_data = False
            for fid in fids:
                v = clean_num(get_row(sheet, fid).get(p))
                if v is not None:
                    total += v
                    has_data = True
            res[p] = total if has_data else None
        return res

    # CDKT - Nature-based mapping
    # Tiền: Main row or Sum(Cash + Equivalents)
    tien_tuong_duong = get_row(cdkt, "cdkt_tien_va_tuong_duong_tien")
    if all(clean_num(v) is None for v in tien_tuong_duong.values):
        tien_tuong_duong = sum_nature(cdkt, "cdkt_tien", "cdkt_cac_khoan_tuong_duong_tien")

    dt_ngan_han = get_row(cdkt, "cdkt_dau_tu_ngan_han")
    phai_thu = get_row(cdkt, "cdkt_cac_khoan_phai_thu")
    ton_kho = get_row(cdkt, "cdkt_hang_ton_kho_rong")
    tscd = get_row(cdkt, "cdkt_tai_san_co_dinh")
    ts_dodang = get_row(cdkt, "cdkt_tai_san_do_dang_dai_han")
    tong_ts = get_row(cdkt, "cdkt_tong_cong_tai_san")
    
    vay_dh = get_row(cdkt, "cdkt_vay_dai_han")
    vay_nh = get_row(cdkt, "cdkt_vay_ngan_han")
    phai_tra_nb = get_row(cdkt, "cdkt_phai_tra_nguoi_ban")
    nguoi_mua_tt = get_row(cdkt, "cdkt_nguoi_mua_tra_tien_truoc")
    
    # Vốn góp & Lãi chưa phân phối - Try common alternatives
    von_gop = get_row(cdkt, "cdkt_von_gop")
    if all(clean_num(v) is None for v in von_gop.values):
        von_gop = get_row(cdkt, "cdkt_von_dau_tu_cua_chu_so_huu")

    lai_cpp = get_row(cdkt, "cdkt_lai_chua_phan_phoi")
    if all(clean_num(v) is None for v in lai_cpp.values):
        # Try components if main row missing
        lai_cpp = sum_nature(cdkt, "cdkt_lnst_chua_phan_phoi_luy_ke_den_cuoi_ky_truoc", "cdkt_lnst_chua_phan_phoi_ky_nay")

    tong_nv = get_row(cdkt, "cdkt_tong_cong_nguon_von")
    
    nguoi_mua_tt_nh = get_row(cdkt, "cdkt_nguoi_mua_tra_tien_truoc")
    nguoi_mua_tt_dh = get_row(cdkt, "cdkt_nguoi_mua_tra_tien_truoc_dai_han")
    dt_cth = get_row(cdkt, "cdkt_doanh_thu_chua_thuc_hien")
    dt_cth_nh = get_row(cdkt, "cdkt_doanh_thu_chua_thuc_hien_ngan_han")
    co_phieu_pt = get_row(cdkt, "cdkt_co_phieu_pho_thong")
    
    # KQKD - Nature-based mapping
    dt_thuan = get_row(kqkd, "kqkd_doanh_thu_thuan")
    ln_gop = get_row(kqkd, "kqkd_loi_nhuan_gop")
    cp_bh = get_row(kqkd, "kqkd_chi_phi_ban_hang")
    cp_qldn = get_row(kqkd, "kqkd_chi_phi_quan_ly_doanh_nghiep")
    dt_tc = get_row(kqkd, "kqkd_doanh_thu_hoat_dong_tai_chinh")
    cp_tc = get_row(kqkd, "kqkd_chi_phi_tai_chinh")
    ln_ld = get_row(kqkd, "kqkd_phan_loi_nhuan_lo_trong_cong_ty_lien_doanh_lien_ket")
    tn_khac = get_row(kqkd, "kqkd_thu_nhap_khac")
    
    # Lãi ròng của cổ đông mẹ (PAT-MI)
    ln_codong_me = get_row(kqkd, "kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me")
    if all(clean_num(v) is None for v in ln_codong_me.values):
        # Fallback to total PAT if minority interest is likely zero or not reported separately
        ln_codong_me = get_row(kqkd, "kqkd_loi_nhuan_sau_thuy_thu_nhap_doanh_nghiep")
    
    # LCTT
    lctt_kd = get_row(lctt, "lctt_luu_chuyen_tien_thuan_tu_hoat_dong_kinh_doanh")
    lctt_dt = get_row(lctt, "lctt_luu_chuyen_tien_thuan_tu_hoat_dong_dau_tu")
    lctt_tc = get_row(lctt, "lctt_luu_chuyen_tien_thuan_tu_hoat_dong_tai_chinh")
    lctt_thuan = get_row(lctt, "lctt_luu_chuyen_tien_thuan_trong_ky")

    add_row("g1", "1) Cấu Trúc Tài Sản", "", 0, lambda p: None)
    add_row("g1_1", "Tiền và tương đương tiền", "tỷ đồng", 1, lambda p: clean_num(tien_tuong_duong.get(p)))
    add_row("g1_2", "Đầu tư ngắn hạn", "tỷ đồng", 1, lambda p: clean_num(dt_ngan_han.get(p)))
    add_row("g1_3", "Các khoản phải thu", "tỷ đồng", 1, lambda p: clean_num(phai_thu.get(p)))
    add_row("g1_4", "Hàng tồn kho, ròng", "tỷ đồng", 1, lambda p: clean_num(ton_kho.get(p)))
    add_row("g1_5", "Tài sản cố định", "tỷ đồng", 1, lambda p: clean_num(tscd.get(p)))
    add_row("g1_6", "Tài sản dở dang dài hạn", "tỷ đồng", 1, lambda p: clean_num(ts_dodang.get(p)))
    
    def calc_ts_khac(p):
        tts = clean_num(tong_ts.get(p))
        if tts is None: return None
        components = sum(clean_num(x.get(p)) or 0 for x in [tien_tuong_duong, dt_ngan_han, phai_thu, ton_kho, tscd, ts_dodang])
        return tts - components

    add_row("g1_7", "Tài sản khác (Phần còn lại)", "tỷ đồng", 1, calc_ts_khac)
    add_row("g1_8", "TỔNG CỘNG TÀI SẢN", "tỷ đồng", 0, lambda p: clean_num(tong_ts.get(p)))

    add_row("g2", "2) Cấu Trúc Nguồn Vốn", "", 0, lambda p: None)
    add_row("g2_1", "Vay dài hạn", "tỷ đồng", 1, lambda p: clean_num(vay_dh.get(p)))
    add_row("g2_2", "Vay ngắn hạn", "tỷ đồng", 1, lambda p: clean_num(vay_nh.get(p)))
    
    def calc_no_chiem_dung(p):
        a = clean_num(phai_tra_nb.get(p))
        b = clean_num(nguoi_mua_tt.get(p))
        if a is None and b is None: return None
        return (a or 0) + (b or 0)
        
    add_row("g2_3", "Nợ chiếm dụng (bao gồm a+b)", "tỷ đồng", 1, calc_no_chiem_dung)
    add_row("g2_3a", "a) Phải trả người bán", "tỷ đồng", 2, lambda p: clean_num(phai_tra_nb.get(p)))
    add_row("g2_3b", "b) Người mua trả tiền trước", "tỷ đồng", 2, lambda p: clean_num(nguoi_mua_tt.get(p)))
    
    add_row("g2_4", "Vốn góp", "tỷ đồng", 1, lambda p: clean_num(von_gop.get(p)))
    add_row("g2_5", "Lãi chưa phân phối", "tỷ đồng", 1, lambda p: clean_num(lai_cpp.get(p)))
    
    no_phai_tra = get_row(cdkt, "cdkt_no_phai_tra")
    von_csh = get_row(cdkt, "cdkt_von_chu_so_huu")
    
    def calc_tong_nguon_von(p):
        v1 = clean_num(tong_nv.get(p))
        if v1 is not None:
             return v1
        npt = clean_num(no_phai_tra.get(p))
        vcsh = clean_num(von_csh.get(p))
        if npt is not None or vcsh is not None:
            return (npt or 0) + (vcsh or 0)
        return None

    def calc_vcsh_khac(p):
        tnv = clean_num(von_csh.get(p))
        if tnv is None: return None
        components = sum(clean_num(x.get(p)) or 0 for x in [von_gop, lai_cpp])
        return tnv - components

    add_row("g2_6", "VCSH khác (Phần còn lại)", "tỷ đồng", 1, calc_vcsh_khac)
    add_row("g2_7", "Tổng cộng nguồn vốn", "tỷ đồng", 0, calc_tong_nguon_von)

    add_row("g3", "3) Khoản Khách hàng trả trước", "", 0, lambda p: None)
    add_row("g3_1", "Người mua trả tiền trước (a+b)", "tỷ đồng", 1, lambda p: clean_num(nguoi_mua_tt.get(p)))
    add_row("g3_1a", "a) Người mua trả tiền trước ngắn hạn", "tỷ đồng", 2, lambda p: clean_num(nguoi_mua_tt_nh.get(p)))
    add_row("g3_1b", "b) Người mua trả tiền trước dài hạn", "tỷ đồng", 2, lambda p: clean_num(nguoi_mua_tt_dh.get(p)))
    add_row("g3_2", "Doanh thu chưa thực hiện (c+d)", "tỷ đồng", 1, lambda p: clean_num(dt_cth.get(p)))
    add_row("g3_2c", "c) Doanh thu chưa thực hiện ngắn hạn", "tỷ đồng", 2, lambda p: clean_num(dt_cth_nh.get(p)))
    
    dt_cth_dh = get_row(cdkt, "cdkt_doanh_thu_chua_thuc_hien_dai_han")
    add_row("g3_2d", "d) Doanh thu chưa thực hiện dài hạn", "tỷ đồng", 2, lambda p: clean_num(dt_cth_dh.get(p)))

    add_row("g4", "4) Lưu chuyển tiền tệ", "", 0, lambda p: None)
    add_row("g4_1", "LCTT từ hoạt động kinh doanh", "tỷ đồng", 1, lambda p: clean_num(lctt_kd.get(p)))
    add_row("g4_2", "LCTT từ hoạt động đầu tư", "tỷ đồng", 1, lambda p: clean_num(lctt_dt.get(p)))
    add_row("g4_3", "LCTT từ hoạt động tài chính", "tỷ đồng", 1, lambda p: clean_num(lctt_tc.get(p)))
    add_row("g4_4", "Lưu chuyển tiền thuần trong kỳ", "tỷ đồng", 1, lambda p: clean_num(lctt_thuan.get(p)))

    add_row("g5", "5) Hiệu quả kinh doanh", "", 0, lambda p: None)
    add_row("g5_1", "Doanh thu thuần", "tỷ đồng", 1, lambda p: clean_num(dt_thuan.get(p)))
    add_row("g5_2", "Lợi nhuận Cổ đông Công ty mẹ", "tỷ đồng", 1, lambda p: clean_num(ln_codong_me.get(p)))
    add_row("g5_3", "Lợi nhuận gộp", "tỷ đồng", 1, lambda p: clean_num(ln_gop.get(p)))
    
    def calc_bien_lng(p):
        d = clean_num(dt_thuan.get(p))
        g = clean_num(ln_gop.get(p))
        if d and d != 0 and g is not None:
            return (g / d) * 100
        return None
        
    add_row("g5_4", "Biên lợi nhuận gộp", "%", 1, calc_bien_lng)

    def calc_bien_ln_me(p):
        d = clean_num(dt_thuan.get(p))
        m = clean_num(ln_codong_me.get(p))
        if d and d != 0 and m is not None:
            return (m / d) * 100
        return None
        
    add_row("g5_5", "Biên LN Cổ đông Công ty mẹ", "%", 1, calc_bien_ln_me)

    add_row("g6", "6) Cấu trúc Lợi nhuận & Chi phí", "", 0, lambda p: None)
    def calc_ln_cot_loi(p):
        g = clean_num(ln_gop.get(p))
        bh = clean_num(cp_bh.get(p))
        ql = clean_num(cp_qldn.get(p))
        if g is None: return None
        return g - (bh or 0) - (ql or 0)

    add_row("g6_1", "Lợi nhuận cốt lõi (a-b)", "tỷ đồng", 1, calc_ln_cot_loi)
    add_row("g6_1a", "a) Lợi nhuận gộp", "tỷ đồng", 2, lambda p: clean_num(ln_gop.get(p)))
    
    def calc_cp_bh_ql(p):
        bh = clean_num(cp_bh.get(p))
        ql = clean_num(cp_qldn.get(p))
        if bh is None and ql is None: return None
        return (bh or 0) + (ql or 0)
        
    add_row("g6_1b", "b) Chi phí bán hàng và QLDN", "tỷ đồng", 2, calc_cp_bh_ql)
    add_row("g6_1b1", "b.1 Chi phí bán hàng", "tỷ đồng", 3, lambda p: clean_num(cp_bh.get(p)))
    add_row("g6_1b2", "b.2 Chi phí quản lý doanh nghiệp", "tỷ đồng", 3, lambda p: clean_num(cp_qldn.get(p)))
    
    add_row("g6_tc", "Lợi nhuận tài chính", "tỷ đồng", 1, lambda p: (clean_num(dt_tc.get(p)) or 0) - (clean_num(cp_tc.get(p)) or 0) if clean_num(dt_tc.get(p)) is not None or clean_num(cp_tc.get(p)) is not None else None)
    add_row("g6_tc1", "Doanh thu hoạt động tài chính", "tỷ đồng", 2, lambda p: clean_num(dt_tc.get(p)))
    add_row("g6_tc2", "Chi phí tài chính", "tỷ đồng", 2, lambda p: clean_num(cp_tc.get(p)))
    add_row("g6_tc3", "Lãi/(lỗ) từ công ty liên doanh", "tỷ đồng", 1, lambda p: clean_num(ln_ld.get(p)))
    add_row("g6_tc4", "Thu nhập, ròng khác", "tỷ đồng", 1, lambda p: clean_num(tn_khac.get(p)))

def calc_bank_metrics(periods, cdkt, kqkd, lctt, get_row, clean_num, add_row):
    """
    Bộ chỉ số Ngân Hàng - Theo format yêu cầu Cấu trúc tương đương.
    """
    tong_ts = get_row(cdkt, "cdkt_bank_tong_tai_san")
    tien = get_row(cdkt, "cdkt_bank_tien_mat_vang_bac_da_quy")
    tien_nhnn = get_row(cdkt, "cdkt_bank_tien_gui_tai_ngan_hang_nha_nuoc_viet_nam")
    tien_tctd = get_row(cdkt, "cdkt_bank_tien_gui_tai_cac_to_chuc_tin_dung_khac_va_cho_vay_cac_tctd_khac")
    cho_vay = get_row(cdkt, "cdkt_bank_cho_vay_khach_hang")
    ck_kd = get_row(cdkt, "cdkt_bank_chung_khoan_kinh_doanh")
    ck_dt = get_row(cdkt, "cdkt_bank_chung_khoan_dau_tu")
    tscd = get_row(cdkt, "cdkt_bank_tai_san_co_dinh")
    
    tien_gui_kh = get_row(cdkt, "cdkt_bank_tien_gui_cua_khach_hang")
    gtcg = get_row(cdkt, "cdkt_bank_phat_hanh_giay_to_co_gia")
    von_csh = get_row(cdkt, "cdkt_bank_von_chu_so_huu")
    tong_nv = get_row(cdkt, "cdkt_bank_no_phai_tra_va_von_chu_so_huu")
    ln_cpp = get_row(cdkt, "cdkt_bank_loi_nhuan_chua_phan_phoi")
    von_dieu_le = get_row(cdkt, "cdkt_bank_von_dieu_le")
    
    toi = get_row(kqkd, "kqkd_bank_tong_thu_nhap_hoat_dong")
    nii = get_row(kqkd, "kqkd_bank_thu_nhap_lai_thuan")
    lai_dv = get_row(kqkd, "kqkd_bank_lailo_thuan_tu_hoat_dong_dich_vu")
    cp_dp = get_row(kqkd, "kqkd_bank_trich_lap_du_phong_ton_that_tin_dung")
    lntt = get_row(kqkd, "kqkd_bank_tong_loi_nhuanlo_truoc_thue")
    
    # Lãi ròng cổ đông mẹ
    ln_rong = get_row(kqkd, "kqkd_bank_co_dong_cua_cong_ty_me")
    if all(clean_num(v) is None for v in ln_rong.values):
        ln_rong = get_row(kqkd, "kqkd_bank_loi_nhuan_sau_thue_thu_nhap_doanh_nghiep")

    lctt_kd = get_row(lctt, "lctt_bank_luu_chuyen_tien_thuan_tu_cac_hoat_dong_san_xuat_kinh_do")
    lctt_dt = get_row(lctt, "lctt_bank_luu_chuyen_tien_thuan_tu_hoat_dong_dau_tu")
    lctt_thuan = get_row(lctt, "lctt_bank_luu_chuyen_tien_thuan_trong_ky")

    add_row("bank_1", "1) Cấu Trúc Tài Sản Ngân Hàng", "", 0, lambda p: None)
    
    def calc_tien_tuong_duong_bank(p):
        v1 = clean_num(tien.get(p)) or 0
        v2 = clean_num(tien_nhnn.get(p)) or 0
        v3 = clean_num(tien_tctd.get(p)) or 0
        return v1 + v2 + v3 if (v1 or v2 or v3) else None

    add_row("bank_1_1", "Tiền, vàng và tiền gửi tại NHNN/TCTD", "tỷ đồng", 1, calc_tien_tuong_duong_bank)
    add_row("bank_1_2", "Cho vay khách hàng", "tỷ đồng", 1, lambda p: clean_num(cho_vay.get(p)))
    
    def calc_invest_bank(p):
        v1 = clean_num(ck_kd.get(p)) or 0
        v2 = clean_num(ck_dt.get(p)) or 0
        return v1 + v2 if (v1 or v2) else None
        
    add_row("bank_1_3", "Chứng khoán kinh doanh & đầu tư", "tỷ đồng", 1, calc_invest_bank)
    add_row("bank_1_4", "Tài sản cố định", "tỷ đồng", 1, lambda p: clean_num(tscd.get(p)))
    
    def calc_ts_khac_bank(p):
        t = clean_num(tong_ts.get(p))
        if t is None: return None
        c1 = calc_tien_tuong_duong_bank(p) or 0
        c2 = clean_num(cho_vay.get(p)) or 0
        c3 = calc_invest_bank(p) or 0
        c4 = clean_num(tscd.get(p)) or 0
        return t - (c1 + c2 + c3 + c4)

    add_row("bank_1_5", "Tài sản khác (Phần còn lại)", "tỷ đồng", 1, calc_ts_khac_bank)
    add_row("bank_1_6", "TỔNG CỘNG TÀI SẢN", "tỷ đồng", 0, lambda p: clean_num(tong_ts.get(p)))

    add_row("bank_2", "2) Nguồn Vốn Huy Động", "", 0, lambda p: None)
    add_row("bank_2_1", "Tiền gửi của khách hàng", "tỷ đồng", 1, lambda p: clean_num(tien_gui_kh.get(p)))
    add_row("bank_2_2", "Phát hành giấy tờ có giá", "tỷ đồng", 1, lambda p: clean_num(gtcg.get(p)))
    add_row("bank_2_3", "Vốn chủ sở hữu", "tỷ đồng", 1, lambda p: clean_num(von_csh.get(p)))
    add_row("bank_2_4", "Lợi nhuận chưa phân phối", "tỷ đồng", 1, lambda p: clean_num(ln_cpp.get(p)))
    
    def calc_nv_khac(p):
        t = clean_num(tong_nv.get(p))
        if t is None: return None
        c1 = clean_num(tien_gui_kh.get(p)) or 0
        c2 = clean_num(gtcg.get(p)) or 0
        c3 = clean_num(von_csh.get(p)) or 0
        return t - (c1 + c2 + c3)

    add_row("bank_2_5", "Nguồn vốn khác (Phần còn lại)", "tỷ đồng", 1, calc_nv_khac)
    add_row("bank_2_6", "TỔNG CỘNG NGUỒN VỐN", "tỷ đồng", 0, lambda p: clean_num(tong_nv.get(p)))

    add_row("bank_3", "3) Lưu chuyển tiền tệ", "", 0, lambda p: None)
    add_row("bank_3_1", "LCTT từ hoạt động kinh doanh", "tỷ đồng", 1, lambda p: clean_num(lctt_kd.get(p)))
    add_row("bank_3_2", "LCTT từ hoạt động đầu tư", "tỷ đồng", 1, lambda p: clean_num(lctt_dt.get(p)))
    add_row("bank_3_3", "Lưu chuyển tiền thuần trong kỳ", "tỷ đồng", 1, lambda p: clean_num(lctt_thuan.get(p)))

    add_row("bank_4", "4) Hiệu quả hoạt động cốt lõi", "", 0, lambda p: None)
    add_row("bank_4_1", "Tổng thu nhập hoạt động (TOI)", "tỷ đồng", 1, lambda p: clean_num(toi.get(p)))
    add_row("bank_4_2", "Thu nhập Lãi Thuần (NII)", "tỷ đồng", 1, lambda p: clean_num(nii.get(p))) # Changed dtt to nii
    add_row("bank_4_3", "Chi phí dự phòng rủi ro tín dụng", "tỷ đồng", 1, lambda p: clean_num(cp_dp.get(p)))
    add_row("bank_4_4", "Tổng lợi nhuận trước thuế", "tỷ đồng", 1, lambda p: clean_num(lntt.get(p)))
    add_row("bank_4_5", "Lợi nhuận Cổ đông Công ty mẹ", "tỷ đồng", 1, lambda p: clean_num(ln_rong.get(p)))
    
    def calc_nim_approx(p):
        lai = clean_num(nii.get(p)) # Changed dtt to nii
        ts = clean_num(tong_ts.get(p))
        if lai and ts and ts != 0:
            return (lai / ts) * 100 * 4 # Annualized
        return None
        
    add_row("bank_4_6", "Biên lãi ròng (NIM) Ước tính", "%", 1, calc_nim_approx)

def calc_sec_metrics(periods, cdkt, kqkd, lctt, get_row, clean_num, add_row):
    """
    Bộ chỉ số tính toán Chứng Khoán - Tương đương các group chung
    """
    tong_ts = get_row(cdkt, "cdkt_sec_tong_cong_tai_san")
    tien = get_row(cdkt, "cdkt_sec_tien_va_tuong_duong_tien")
    fvtpl = get_row(cdkt, "cdkt_sec_cac_tai_san_tai_chinh_ghi_nhan_thong_qua_lai_lo")
    cho_vay = get_row(cdkt, "cdkt_sec_cac_khoan_cho_vay") # margin
    afs = get_row(cdkt, "cdkt_sec_cac_khoan_tai_chinh_san_sang_de_ban")
    htm = get_row(cdkt, "cdkt_sec_cac_khoan_dau_tu_nam_giu_den_ngay_dao_han")
    tscd = get_row(cdkt, "cdkt_sec_tai_san_co_dinh")
    
    vay_nh = get_row(cdkt, "cdkt_sec_vay_va_no_thue_tai_san_tai_chinh_ngan_han")
    vay_dh = get_row(cdkt, "cdkt_sec_vay_va_no_thue_tai_san_tai_chinh_dai_han")
    von_csh = get_row(cdkt, "cdkt_sec_von_chu_so_huu")
    tong_nv = get_row(cdkt, "cdkt_sec_tong_cong_nguon_von")
    ln_cpp = get_row(cdkt, "cdkt_sec_loi_nhuan_chua_phan_phoi")
    von_gop = get_row(cdkt, "cdkt_sec_von_gop")

    dt_hd = get_row(kqkd, "kqkd_sec_doanh_thu_hoat_dong")
    dt_mg = get_row(kqkd, "kqkd_sec_doanh_thu_nghiep_vu_moi_gioi_chung_khoan")
    lai_fvtpl = get_row(kqkd, "kqkd_sec_lai_tu_cac_tai_san_tai_chinh_ghi_nhan_thong_qua_lailo")
    lai_cho_vay = get_row(kqkd, "kqkd_sec_lai_tu_cac_khoan_cho_vay_va_phai_thu")
    cp_hd = get_row(kqkd, "kqkd_sec_chi_phi_hoat_dong")
    lntt = get_row(kqkd, "kqkd_sec_tong_loi_nhuan_ke_toan_truoc_thue")
    
    # Lãi ròng cổ đông mẹ
    ln_rong = get_row(kqkd, "kqkd_sec_loi_nhuan_sau_thue_phan_bo_cho_chu_so_huu")
    if all(clean_num(v) is None for v in ln_rong.values):
        ln_rong = get_row(kqkd, "kqkd_sec_loi_nhuan_sau_thue_thu_nhap_doanh_nghiep")

    lctt_kd = get_row(lctt, "lctt_sec_luu_chuyen_thuan_tu_hoat_dong_kinh_doanh")
    lctt_dt = get_row(lctt, "lctt_sec_luu_chuyen_tien_thuan_tu_hoat_dong_dau_tu")
    lctt_tc = get_row(lctt, "lctt_sec_luu_chuyen_thuan_tu_hoat_dong_tai_chinh")
    lctt_thuan = get_row(lctt, "lctt_sec_luu_chuyen_tien_thuan_trong_ky")

    add_row("sec_1", "1) Cấu Trúc Tài Sản CTCK", "", 0, lambda p: None)
    add_row("sec_1_1", "Tiền và tương đương tiền", "tỷ đồng", 1, lambda p: clean_num(tien.get(p)))
    
    def calc_invest_sec(p):
        v1 = clean_num(fvtpl.get(p)) or 0
        v2 = clean_num(afs.get(p)) or 0
        v3 = clean_num(htm.get(p)) or 0
        return v1 + v2 + v3 if (v1 or v2 or v3) else None

    add_row("sec_1_2", "Tài sản tài chính (FVTPL+AFS+HTM)", "tỷ đồng", 1, calc_invest_sec)
    add_row("sec_1_3", "Các khoản cho vay (Margin)", "tỷ đồng", 1, lambda p: clean_num(cho_vay.get(p)))
    add_row("sec_1_4", "Tài sản cố định", "tỷ đồng", 1, lambda p: clean_num(tscd.get(p)))
    
    def calc_ts_khac_sec(p):
        t = clean_num(tong_ts.get(p))
        if t is None: return None
        c1 = clean_num(tien.get(p)) or 0
        c2 = calc_invest_sec(p) or 0
        c3 = clean_num(cho_vay.get(p)) or 0
        c4 = clean_num(tscd.get(p)) or 0
        return t - (c1 + c2 + c3 + c4)

    add_row("sec_1_5", "Tài sản khác (Phần còn lại)", "tỷ đồng", 1, calc_ts_khac_sec)
    add_row("sec_1_6", "TỔNG CỘNG TÀI SẢN", "tỷ đồng", 0, lambda p: clean_num(tong_ts.get(p)))

    add_row("sec_2", "2) Nguồn Vốn CTCK", "", 0, lambda p: None)
    
    def calc_vay_sec(p):
        v1 = clean_num(vay_nh.get(p)) or 0
        v2 = clean_num(vay_dh.get(p)) or 0
        return v1 + v2 if (v1 or v2) else None
        
    add_row("sec_2_1", "Vay nợ (Ngắn + Dài hạn)", "tỷ đồng", 1, calc_vay_sec)
    add_row("sec_2_2", "Vốn góp chủ sở hữu", "tỷ đồng", 1, lambda p: clean_num(von_gop.get(p)))
    add_row("sec_2_3", "Lợi nhuận chưa phân phối", "tỷ đồng", 1, lambda p: clean_num(ln_cpp.get(p)))
    
    def calc_nv_khac_sec(p):
        t = clean_num(tong_nv.get(p))
        if t is None: return None
        c1 = calc_vay_sec(p) or 0
        c2 = clean_num(von_csh.get(p)) or 0 # Use von_csh for total equity component
        return t - (c1 + c2)

    add_row("sec_2_4", "Nợ chiếm dụng & Khác", "tỷ đồng", 1, calc_nv_khac_sec)
    add_row("sec_2_5", "TỔNG CỘNG NGUỒN VỐN", "tỷ đồng", 0, lambda p: clean_num(tong_nv.get(p)))

    add_row("sec_3", "3) Lưu chuyển tiền tệ", "", 0, lambda p: None)
    add_row("sec_3_1", "LCTT từ hoạt động kinh doanh", "tỷ đồng", 1, lambda p: clean_num(lctt_kd.get(p)))
    add_row("sec_3_2", "LCTT từ hoạt động đầu tư", "tỷ đồng", 1, lambda p: clean_num(lctt_dt.get(p)))
    add_row("sec_3_3", "Lưu chuyển tiền thuần trong kỳ", "tỷ đồng", 1, lambda p: clean_num(lctt_thuan.get(p)))

    add_row("sec_4", "4) Hiệu quả kinh doanh CTCK", "", 0, lambda p: None)
    add_row("sec_4_1", "Tổng doanh thu hoạt động", "tỷ đồng", 1, lambda p: clean_num(dt_hd.get(p)))
    add_row("sec_4_2", "Doanh thu môi giới", "tỷ đồng", 1, lambda p: clean_num(dt_mg.get(p)))
    add_row("sec_4_3", "Lãi từ các TS tài chính (FVTPL)", "tỷ đồng", 1, lambda p: clean_num(lai_fvtpl.get(p)))
    add_row("sec_4_4", "Lãi từ các khoản cho vay", "tỷ đồng", 1, lambda p: clean_num(lai_cho_vay.get(p)))
    add_row("sec_4_5", "Lợi nhuận Cổ đông Công ty mẹ", "tỷ đồng", 1, lambda p: clean_num(ln_rong.get(p)))
    
    def calc_bien_ln_sec(p):
        d = clean_num(dt_hd.get(p))
        m = clean_num(ln_rong.get(p))
        if d and d != 0 and m is not None:
            return (m / d) * 100
        return None
        
    add_row("sec_4_6", "Biên LN ròng / DT hoạt động", "%", 1, calc_bien_ln_sec)

def calc_metrics(ticker: str, period: str) -> pd.DataFrame:
    """Entry point for calculating metrics based on sector."""
    # Phase 4: Load sector-specific sheets
    from sector import SECTOR_SHEETS
    ticker_sector = get_sector(ticker)
    sheet_map = SECTOR_SHEETS.get(ticker_sector, SECTOR_SHEETS["normal"])
    
    # sheet_map is list of (API_section, sheet_id) tuples
    # We need: cdkt sheet, kqkd sheet, lctt sheet
    cdkt_sheet = next((s[1].lower() for s in sheet_map if "BALANCE" in s[0]), "cdkt")
    kqkd_sheet = next((s[1].lower() for s in sheet_map if "INCOME" in s[0]), "kqkd")
    lctt_sheet = next((s[1].lower() for s in sheet_map if "CASH" in s[0]), "lctt")
    
    try:
        cdkt = load_tab_from_supabase(ticker, period, cdkt_sheet)
        kqkd = load_tab_from_supabase(ticker, period, kqkd_sheet)
        lctt = load_tab_from_supabase(ticker, period, lctt_sheet)
    except Exception as e:
        print(f"  ❌ Cannot load supabase data: {e}")
        return pd.DataFrame()

    if cdkt.empty or kqkd.empty or lctt.empty:
        return pd.DataFrame()

    meta_cols = ["field_id", "vn_name", "unit", "level"]
    cdkt_p = set(c for c in cdkt.columns if c not in meta_cols)
    kqkd_p = set(c for c in kqkd.columns if c not in meta_cols)
    lctt_p = set(c for c in lctt.columns if c not in meta_cols)
    
    def sort_p(p):
        if str(p).startswith("Q"):
            try: return (int(p[3:]), int(p[1]))
            except: pass
        try: return (int(p), 0)
        except: return (0, 0)

    periods = sorted(list(cdkt_p & kqkd_p & lctt_p), key=sort_p, reverse=True)

    if not periods:
        return pd.DataFrame()

    def get_row(df, fid):
        sub = df[df["field_id"] == fid]
        if sub.empty: return pd.Series(None, index=periods)
        return sub.iloc[0]

    def clean_num(val):
        if val is None or (isinstance(val, float) and pd.isna(val)) or val == "":
            return None
        try: return float(val)
        except (ValueError, TypeError): return None

    rows = []
    row_counter = 0
    
    def add_row(fid, vn_name, unit, level, calc_func):
        nonlocal row_counter
        row_counter += 1
        row_dict = {"item_id": fid, "vn_name": vn_name, "unit": unit, "level": level, "row_number": row_counter}
        for p in periods:
            row_dict[p] = calc_func(p)
        rows.append(row_dict)

    # Sector Routing (Phase 2: centralized via sector.py)
    ticker_sector = get_sector(ticker)
    is_bank = ticker_sector == "bank"
    is_sec = ticker_sector == "sec"

    if is_bank:
        calc_bank_metrics(periods, cdkt, kqkd, lctt, get_row, clean_num, add_row)
    elif is_sec:
        calc_sec_metrics(periods, cdkt, kqkd, lctt, get_row, clean_num, add_row)
    else:
        calc_normal_metrics(periods, cdkt, kqkd, lctt, get_row, clean_num, add_row)

    # Common metrics for all sectors (EPS, Growth)
    add_row("g7", "7) Tăng trưởng Doanh thu & Lãi ròng", "", 0, lambda p: None)
    
    if is_bank:
        ln_codong_me = get_row(kqkd, "kqkd_bank_co_dong_cua_cong_ty_me")
        dt_thuan = get_row(kqkd, "kqkd_bank_tong_thu_nhap_hoat_dong")
        von_dieu_le = get_row(cdkt, "cdkt_bank_von_dieu_le")
        # Estimate share count from charter capital (10,000 VND / share), value in bill VND
        co_phieu_pt_data = {p: int((clean_num(von_dieu_le.get(p)) * 1000000000) / 10000) if clean_num(von_dieu_le.get(p)) else None for p in periods}
        co_phieu_pt = pd.Series(co_phieu_pt_data)
    elif is_sec:
        ln_codong_me = get_row(kqkd, "kqkd_sec_loi_nhuan_sau_thue_phan_bo_cho_chu_so_huu")
        dt_thuan = get_row(kqkd, "kqkd_sec_doanh_thu_hoat_dong")
        co_phieu_pt = get_row(cdkt, "cdkt_sec_co_phieu_dang_luu_hanh")
    else:
        ln_codong_me = get_row(kqkd, "kqkd_loi_nhuan_cua_co_dong_cua_cong_ty_me")
        dt_thuan = get_row(kqkd, "kqkd_doanh_thu_thuan")
        co_phieu_pt = get_row(cdkt, "cdkt_co_phieu_pho_thong")
    
    def calc_yoy(val_current, val_prev):
        if val_current is not None and val_prev and val_prev != 0:
            return ((val_current - val_prev) / abs(val_prev)) * 100
        return None
        
    def get_yoy_period(p):
        if period == "year":
            try: return str(int(p) - 1)
            except: return None
        elif period == "quarter" and len(p) >= 7:
            try:
                q = int(p[1])
                y = int(p[3:])
                return f"Q{q}/{y-1}"
            except: return None
        return None

    def calc_tt_dt(p):
        prev = get_yoy_period(p)
        if prev in periods:
            return calc_yoy(clean_num(dt_thuan.get(p)), clean_num(dt_thuan.get(prev)))
        return None

    def calc_tt_ln(p):
        prev = get_yoy_period(p)
        if prev in periods:
            return calc_yoy(clean_num(ln_codong_me.get(p)), clean_num(ln_codong_me.get(prev)))
        return None
        
    add_row("g7_1", "Tăng trưởng Doanh thu (YoY)", "%", 1, calc_tt_dt)
    add_row("g7_2", "Tăng trưởng Lãi ròng (YoY)", "%", 1, calc_tt_ln)

    # Cổ phiếu & Định giá
    add_row("g8", "8) Hiệu quả đầu tư & Cổ phiếu", "", 0, lambda p: None)
    
    def calc_ttm_ln(p):
        if period == "year":
            return clean_num(ln_codong_me.get(p))
        try:
            q = int(p[1])
            y = int(p[3:])
            qs = [p]
            curr_q, curr_y = q, y
            for _ in range(3):
                if curr_q == 1:
                    curr_q = 4
                    curr_y -= 1
                else:
                    curr_q -= 1
                qs.append(f"Q{curr_q}/{curr_y}")
            if all(qid in periods for qid in qs):
                return sum(clean_num(ln_codong_me.get(qid)) or 0 for qid in qs)
        except: pass
        return None

    add_row("g8_1", "LN ròng (TTM)", "tỷ đồng", 1, calc_ttm_ln)
    
    def calc_sl_cp(p):
        v = clean_num(co_phieu_pt.get(p))
        return (v / 10000.0) if v else None
        
    add_row("g8_2", "Số lượng cổ phiếu", "cổ phiếu", 1, calc_sl_cp)
    
    def calc_eps(p):
        ttm = calc_ttm_ln(p)
        sl_cp = calc_sl_cp(p)
        if ttm is not None and sl_cp and sl_cp != 0:
            return ttm / sl_cp
        return None
        
    add_row("g8_3", "EPS (TTM)", "đồng/cp", 1, calc_eps)
    add_row("g8_4", "P/E", "lần", 1, lambda p: None) # Requires current market price
    add_row("g8_5", "Vốn Hóa", "tỷ đồng", 1, lambda p: None) # Requires current market price

    result_df = pd.DataFrame(rows)
    cols = ["item_id", "vn_name", "unit", "level", "row_number"] + periods
    return result_df[cols]

def main():
    parser = argparse.ArgumentParser(description="Finsang V2.0 — Metrics Engine")
    parser.add_argument("--ticker", required=True, help="Stock ticker (e.g., VHC)")
    parser.add_argument("--period", choices=["year", "quarter"], default="year")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    print(f"\n{'═'*80}")
    print(f"  📈 METRICS ENGINE — {ticker} ({args.period.upper()})")
    print(f"{'═'*80}\n")

    df = calc_metrics(ticker, args.period)
    if df.empty:
        return

    periods = [c for c in df.columns if c not in ["item_id", "vn_name", "unit", "level", "row_number"]]
    print_cols = ["Chỉ tiêu"] + periods[:5]
    
    header = f"  {print_cols[0]:<35} | " + " | ".join([f"{c:>10}" for c in print_cols[1:]])
    print(header)
    print(f"  {'-'*80}")

    for _, row in df.iterrows():
        val_strs = []
        for p in print_cols[1:]:
            val = row[p]
            if val is None:
                val_strs.append(f"{'—':>10}")
            elif row["unit"] == "%":
                val_strs.append(f"{val:>9.1f}%")
            elif row["unit"] == "tỷ đồng":
                val = val / 1000000000
                val_strs.append(f"{val:>10.2f}")
            else:
                val_strs.append(f"{val:>10.2f}")
                
        line = f"  {row['vn_name']:<35} | " + " | ".join(val_strs)
        print(line)

    print(f"\n{'═'*80}\n")

if __name__ == "__main__":
    main()

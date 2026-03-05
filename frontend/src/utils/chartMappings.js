/**
 * chartMappings.js
 * Mappings between chart series and Supabase item_ids.
 * Categorized by SECTOR (normal, bank, sec).
 */

export const NORMAL_CHART_MAPPINGS = {
    income_performance: {
        'Doanh thu thuần': 'Doanh thu thuần',
        'Lãi ròng': 'Lãi/(lỗ) thuần sau thuế (LNST)',
        'Biên LN gộp': 'Biên lợi nhuận gộp',
        'Biên lãi ròng': 'Biên LN Cổ đông Công ty mẹ',
    },
    growth: {
        'Tăng trưởng DTT (%)': 'Tăng trưởng Doanh thu (YoY)',
        'Tăng trưởng Lãi ròng (%)': 'Tăng trưởng Lãi ròng (YoY)',
    },
    asset_structure: {
        'Tiền & Tương đương': 'cdkt_tien_va_cac_khoan_tuong_duong_tien',
        'Đầu tư ngắn hạn': 'cdkt_dau_tu_tai_chinh_ngan_han',
        'Phải thu': 'cdkt_cac_khoan_phai_thu_ngan_han',
        'Hàng tồn kho': 'cdkt_hang_ton_kho',
        'TS cố định': 'cdkt_tai_san_co_dinh',
        'TS dở dang': 'cdkt_tai_san_do_dang_dai_han',
        'TS khác': 'cdkt_tai_san_ngan_han_khac',
    },
    capital_structure: {
        'Vay ngắn hạn': 'cdkt_vay_ngan_han',
        'Vay dài hạn': 'cdkt_vay_dai_han',
        'Phải trả người bán': 'cdkt_phai_tra_nguoi_ban',
        'Người mua trả tiền trước': 'cdkt_nguoi_mua_tra_tien_truoc',
        'Vốn góp': 'cdkt_von_gop',
        'Lãi chưa phân phối': 'cdkt_loi_nhuan_sau_thue_chua_phan_phoi',
        'Cổ phiếu quỹ': 'cdkt_co_phieu_quy',
    }
};

export const BANK_CHART_MAPPINGS = {
    income_performance: {
        'Tổng thu nhập': 'Tổng thu nhập hoạt động (TOI)',
        'Lãi ròng': 'LN ròng (TTM)',
        'NIM (%)': 'Biên lãi ròng (NIM) Ước tính',
    },
    credit_growth: {
        'Cho vay khách hàng': 'cdkt_bank_cho_vay_khach_hang',
        'Tiền gửi khách hàng': 'cdkt_bank_tien_gui_cua_khach_hang',
        'g(TOI) (%)': 'Tăng trưởng Doanh thu (YoY)',
        'g(Lãi ròng) (%)': 'Tăng trưởng Lãi ròng (YoY)',
    },
    efficiency: {
        'ROE (%)': 'cstc_roe',
        'ROA (%)': 'cstc_roa',
        'COF (%)': 'Tỷ lệ CIR (%)', // Mapping to CIR since COF isn't calculated
        'YOEA (%)': 'Tỷ lệ LDR — Cho vay / Tiền gửi (%)', // Alternative map for structure
        'CASA (%)': 'Tỷ lệ nợ xấu (%)', // Used in graph, map effectively
    },
    asset_structure: {
        'Tiền & Tiền gửi NHNN': 'cdkt_bank_tien_mat_vang_bac_da_quy',
        'Cho vay khách hàng': 'cdkt_bank_cho_vay_khach_hang',
        'Chứng khoán ĐT': 'cdkt_bank_chung_khoan_dau_tu',
        'TS cố định': 'cdkt_bank_tai_san_co_dinh',
        'Tài sản khác': 'cdkt_bank_tai_san_co_khac',
    },
    npl_structure: {
        'Tỷ lệ nợ xấu (%)': 'bank_4_10',
        'NPL': 'bank_4_10',
    }
};

export const SEC_CHART_MAPPINGS = {
    income_performance: {
        'Tổng doanh thu': 'Tổng doanh thu hoạt động',
        'Lãi ròng': 'Lợi nhuận Cổ đông Công ty mẹ',
        'Biên lãi ròng (%)': 'Biên LN ròng / DT hoạt động',
    },
    revenue_structure: {
        'Môi giới': 'Doanh thu môi giới',
        'Tự doanh (FVTPL)': 'Lãi từ các TS tài chính (FVTPL)',
        'Cho vay (Margin)': 'Lãi từ các khoản cho vay',
    },
    growth: {
        'ROE': 'Tăng trưởng Lãi ròng (YoY)', // Use profit growth as proxy for now
        'ROA': 'Tăng trưởng Doanh thu (YoY)',
        'LCTT KD': 'LCTT từ hoạt động kinh doanh',
    },
    asset_structure: {
        'FVTPL': 'Tài sản tài chính (FVTPL+AFS+HTM)',
        'Margin (Cho vay)': 'Các khoản cho vay (Margin)',
        'Tiền & Tương đương': 'Tiền và tương đương tiền',
    },
    capital_structure: {
        'Vay nợ ngắn hạn': 'Vay nợ (Ngắn + Dài hạn)',
        'Vay nợ dài hạn': 'Nợ chiếm dụng & Khác',
        'VCSH': 'TỔNG CỘNG NGUỒN VỐN',
        'LN chưa pp': 'Lợi nhuận chưa phân phối',
    }
};

export const SECTOR_MAPPINGS = {
    normal: NORMAL_CHART_MAPPINGS,
    bank: BANK_CHART_MAPPINGS,
    sec: SEC_CHART_MAPPINGS,
};

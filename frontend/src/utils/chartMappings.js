/**
 * chartMappings.js
 * Mappings between chart series and Supabase item_ids.
 * Categorized by SECTOR (normal, bank, sec).
 */

export const NORMAL_CHART_MAPPINGS = {
    income_performance: {
        'Doanh thu thuần': 'kqkd_doanh_thu_thuan',
        'Lãi ròng': 'kqkd_loi_nhuan_sau_thuy_thu_nhap_doanh_nghiep',
        'Biên LN gộp': 'g7_3',
        'Biên lãi ròng': 'g7_4',
    },
    growth: {
        'Tăng trưởng DTT (%)': 'g7_1',
        'Tăng trưởng Lãi ròng (%)': 'g7_2',
    },
    asset_structure: {
        'Tiền & Tương đương': 'g1_1',
        'Đầu tư ngắn hạn': 'g1_2',
        'Phải thu': 'g1_3',
        'Hàng tồn kho': 'g1_4',
        'TS cố định': 'g1_5',
        'TS dở dang': 'g1_6',
        'TS khác': 'g1_7',
    },
    capital_structure: {
        'Vay ngắn hạn': 'g2_1',
        'Vay dài hạn': 'g2_2',
        'Phải trả người bán': 'g2_3',
        'Người mua trả tiền trước': 'g2_4',
        'Vốn góp': 'g2_5',
        'Lãi chưa phân phối': 'g2_6',
        'Nguồn vốn khác': 'g2_7',
    }
};

export const BANK_CHART_MAPPINGS = {
    income_performance: {
        'Tổng thu nhập': 'bank_4_1',
        'Lãi ròng': 'bank_4_5',
        'NIM (%)': 'bank_4_6',
    },
    credit_growth: {
        'Cho vay khách hàng': 'bank_1_2',
        'Tiền gửi khách hàng': 'bank_2_1',
        'g(TOI) (%)': 'g7_1',
        'g(Lãi ròng) (%)': 'g7_2',
    },
    efficiency: {
        'CASA (%)': 'bank_4_7',
        'COF (%)': 'bank_4_8',
        'YOEA (%)': 'bank_4_9',
    },
    asset_structure: {
        'Tiền & Tiền gửi NHNN': 'bank_1_1',
        'Cho vay khách hàng': 'bank_1_2',
        'Chứng khoán ĐT': 'bank_1_3',
        'TS cố định': 'bank_1_4',
        'TS khác': 'bank_1_5',
    },
    npl_structure: {
        'Tỷ lệ nợ xấu (%)': 'bank_4_10',
        'Tỷ lệ CIR (%)': 'bank_4_11',
    }
};

export const SEC_CHART_MAPPINGS = {
    income_performance: {
        'Tổng doanh thu': 'sec_4_1',
        'Lãi ròng': 'sec_4_5',
        'Biên lãi ròng (%)': 'sec_4_6',
    },
    revenue_structure: {
        'Môi giới': 'sec_4_2',
        'Tự doanh (FVTPL)': 'sec_4_3',
        'Cho vay (Margin)': 'sec_4_4',
    },
    growth: {
        'LCTT KD': 'sec_3_1',
        'LCTT ĐT': 'sec_3_2',
        'Tiền thuần': 'sec_3_3',
    },
    asset_structure: {
        'FVTPL': 'sec_1_2',
        'Margin': 'sec_1_3',
        'Tiền & Khác': 'sec_1_1',
    },
    capital_structure: {
        'Vay nợ': 'sec_2_1',
        'VCSH': 'sec_2_2',
        'LN chưa pp': 'sec_2_3',
        'Khác': 'sec_2_4',
    }
};

export const SECTOR_MAPPINGS = {
    normal: NORMAL_CHART_MAPPINGS,
    bank: BANK_CHART_MAPPINGS,
    sec: SEC_CHART_MAPPINGS,
};

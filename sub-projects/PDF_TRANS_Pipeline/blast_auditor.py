import json
import sys
import os

# Import SQLite Staging DB layer
try:
    from staging_db import get_connection, log_audit_result, update_report_status
except ImportError as e:
    print(f"Error loading staging_db: {e}")
    get_connection = None

def normalize_keys(data_dict: dict) -> dict:
    """
    Map các key từ Cty Kiểm Toán (đủ loại tên gọi) sang Finsang Universal Schema
    Ví dụ: 'Doanh thu thuần về bán hàng' -> 'revenue'
    """
    schema_map = {
        "revenue": ["doanh thu thuần", "doanh thu bán hàng và cung cấp dịch vụ", "doanh thu thuần về bán hàng"],
        "cogs": ["giá vốn hàng bán", "giá vốn", "trị giá vốn"],
        "gross_profit": ["lợi nhuận gộp", "lợi nhuận gộp về bán hàng", "lợi nhuận gộp từ bán hàng"],
        "assets": ["tổng cộng tài sản", "tổng tài sản"],
        "liabilities": ["nợ phải trả", "tổng nợ phải trả"],
        "equity": ["vốn chủ sở hữu", "tổng cộng nguồn vốn chủ sở hữu"]
    }
    
    normalized = {}
    for key, value in data_dict.items():
        key_lower = key.lower()
        mapped = False
        for std_key, keywords in schema_map.items():
            if any(kw in key_lower for kw in keywords):
                normalized[std_key] = value
                mapped = True
                break
        
        # Nếu không map được vẫn giữ lại để lưu trữ dưới dạng custom field
        if not mapped:
            normalized[key] = value
            
    return normalized

def audit_record(report_id, normalized_data: dict):
    """
    Tiến hành Audit (CFO Validate).
    Quy tắc 1: Doanh Thu - Giá Vốn = LNTT Gộp (Cho phép chênh lệch < 1%)
    Quy tắc 2: Tổng Tài Sản = Tổng Nợ Phải Trả + Vốn Chủ Sở Hữu (Chênh lệch < 1%)
    """
    if not get_connection:
        return
        
    revenue = float(normalized_data.get("revenue", 0))
    cogs = float(normalized_data.get("cogs", 0))
    gross_profit = float(normalized_data.get("gross_profit", 0))
    
    assets = float(normalized_data.get("assets", 0))
    liabilities = float(normalized_data.get("liabilities", 0))
    equity = float(normalized_data.get("equity", 0))
    
    all_passed = True
    
    # Audit 1: Income Statement Check
    if revenue and gross_profit:
        calc_gross = revenue - cogs
        diff = abs(calc_gross - gross_profit)
        # Chênh lệch > 1%
        if gross_profit != 0 and (diff / abs(gross_profit)) > 0.01:
            all_passed = False
            log_audit_result(report_id, "Gross Profit Equation (Rev - COGS = GP)", False, f"Diff {diff} > 1%. Calc: {calc_gross}, Actual: {gross_profit}")
        else:
            log_audit_result(report_id, "Gross Profit Equation (Rev - COGS = GP)", True, "Passed threshold")
            
    # Audit 2: Balance Sheet Check
    if assets and equity:
        calc_assets = liabilities + equity
        diff = abs(calc_assets - assets)
        if assets != 0 and (diff / abs(assets)) > 0.01:
            all_passed = False
            log_audit_result(report_id, "Balance Sheet Equation (A = L + E)", False, f"Diff {diff} > 1%. Calc: {calc_assets}, Actual: {assets}")
        else:
            log_audit_result(report_id, "Balance Sheet Equation (A = L + E)", True, "Passed threshold")
            
    if all_passed:
        update_report_status(report_id, 'READY_FOR_SYNC')
        print(f"[Audit passed] Report #{report_id} is marked READY_FOR_SYNC.")
    else:
        update_report_status(report_id, 'PENDING_AUDIT')
        print(f"[Audit faled] Report #{report_id} is marked PENDING_AUDIT for CFO review.")

def run_batch_audit():
    if not get_connection:
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, raw_json FROM raw_reports WHERE status = 'PENDING_AUDIT'")
    rows = cursor.fetchall()
    
    if not rows:
        print("No pending records to audit.")
    
    for row in rows:
        report_id = row['id']
        data_dict = json.loads(row['raw_json'])
        normalized = normalize_keys(data_dict)
        audit_record(report_id, normalized)
        
    conn.close()

if __name__ == '__main__':
    print("Testing B.L.A.S.T Auditor...")
    # Mock Database Injection
    from staging_db import insert_raw_report
    mock_data = {
        "Doanh thu thuần": 1000,
        "Giá vốn": 600,
        "Lợi nhuận gộp": 400,
        "Tổng tài sản": 5000,
        "Nợ phải trả": 2000,
        "Vốn chủ sở hữu": 3000
    }
    insert_raw_report("http://sample.pdf", "VNM", "Q1-2024", mock_data)
    run_batch_audit()

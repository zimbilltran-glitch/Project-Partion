import sqlite3
import os
import json
from datetime import datetime

STAGING_DB_PATH = os.path.join(os.path.dirname(__file__), 'staging_pdf_trans.db')

def get_connection():
    """Tạo kết nối tới Staging SQLite Database"""
    conn = sqlite3.connect(STAGING_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo cấu trúc các bảng cho PDF_TRANS Staging Database"""
    conn = get_connection()
    cursor = conn.cursor()

    # Bảng chứa kết quả bóc tách thô từ PDF
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            company_code TEXT,
            report_period TEXT,
            raw_json TEXT NOT NULL,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'PENDING_AUDIT' -- 'PENDING_AUDIT', 'READY_FOR_SYNC', 'REJECTED'
        )
    ''')

    # Bảng chứa kết quả Audit (Kiểm toán CFO)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            audit_rule TEXT NOT NULL,
            passed BOOLEAN NOT NULL,
            details TEXT,
            audited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(report_id) REFERENCES raw_reports(id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Staging database initialized successfully at: {STAGING_DB_PATH}")

def insert_raw_report(source_url, company_code, report_period, raw_data_dict):
    """Lưu dữ liệu thô vào Staging Table"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO raw_reports (source_url, company_code, report_period, raw_json)
        VALUES (?, ?, ?, ?)
    ''', (source_url, company_code, report_period, json.dumps(raw_data_dict, ensure_ascii=False)))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id

def log_audit_result(report_id, audit_rule, passed, details=""):
    """Ghi log kết quả kiểm toán"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_logs (report_id, audit_rule, passed, details)
        VALUES (?, ?, ?, ?)
    ''', (report_id, audit_rule, passed, details))
    conn.commit()
    conn.close()

def update_report_status(report_id, status):
    """Cập nhật trạng thái của báo cáo sau Audit"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE raw_reports
        SET status = ?
        WHERE id = ?
    ''', (status, report_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()

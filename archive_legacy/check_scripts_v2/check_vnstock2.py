try:
    from vnstock import financial_report
    import sys
    
    with open('.tmp/vnstock_schema_out.txt', 'w', encoding='utf-8') as f:
        df_mbb = financial_report(symbol='MBB', report_type='BalanceSheet', frequency='Yearly')
        f.write("--- MBB Balance Sheet ---\n")
        if df_mbb is not None:
            f.write("\n".join(df_mbb.columns.tolist()) + "\n")
            
        df_ssi = financial_report(symbol='SSI', report_type='BalanceSheet', frequency='Yearly')
        f.write("\n--- SSI Balance Sheet ---\n")
        if df_ssi is not None:
            f.write("\n".join(df_ssi.columns.tolist()) + "\n")
            
except Exception as e:
    with open('.tmp/vnstock_schema_out.txt', 'w', encoding='utf-8') as f:
        f.write(f"Error: {e}")

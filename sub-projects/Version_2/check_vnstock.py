try:
    from vnstock import financial_report
    df = financial_report(symbol='MBB', report_type='BalanceSheet', frequency='Yearly')
    print("MBB Balance Sheet columns/rows:")
    print(df.head())
    print("\nColumns:", df.columns.tolist())
    
    # Also dump SSI
    df_s = financial_report(symbol='SSI', report_type='BalanceSheet', frequency='Yearly')
    print("\nSSI Balance Sheet columns:")
    print(df_s.columns.tolist())
except Exception as e:
    print(f"Error: {e}")

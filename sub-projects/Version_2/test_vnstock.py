from vnstock3 import Vnstock

try:
    vns = Vnstock().stock(symbol='MBB', source='VCI')
    df_cdkt = vns.finance.financial_report(report_type='balance_sheet', period='year')
    df_kqkd = vns.finance.financial_report(report_type='income_statement', period='year')
    df_lctt = vns.finance.financial_report(report_type='cash_flow', period='year')
    
    print("CDKT shape:", df_cdkt.shape)
    print("CDKT cols:", df_cdkt.columns.tolist()[:5])
    print("KQKD args:", df_kqkd.shape)
except Exception as e:
    print(f"Error fetching vnstock3: {e}")

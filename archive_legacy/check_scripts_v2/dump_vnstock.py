import sys, json, os

from vnstock3 import Vnstock
def dump_schema(ticker, source='VCI'):
    vns = Vnstock().stock(symbol=ticker, source=source)
    with open(f".tmp/vnstock_{ticker}.txt", "w", encoding="utf-8") as f:
        for report_type in ['balance_sheet', 'income_statement', 'cash_flow']:
            df = vns.finance.financial_report(report_type=report_type, period='year')
            f.write(f"--- {ticker} {report_type} ---\n")
            if df is not None and not df.empty:
                for idx, col in enumerate(df.index):
                    f.write(f"{idx+1}: {col}\n")

dump_schema('MBB')
dump_schema('SSI')

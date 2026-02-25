import os
import sys
import warnings
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Finsang Terminal v2.0",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded",
)

warnings.filterwarnings("ignore")

# ─── 1. Setup Environment & Imports ───────────────────────────────────────────
# Add Version_2 to sys.path so we can import its modules directly
sys.path.insert(0, str(Path(__file__).parent / "Version_2"))

# Load Secrets
# If running on Streamlit Cloud, use st.secrets. Otherwise fallback to .env
try:
    if "FINSANG_ENCRYPTION_KEY" in st.secrets:
        os.environ["FINSANG_ENCRYPTION_KEY"] = st.secrets["FINSANG_ENCRYPTION_KEY"]
except FileNotFoundError:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Now we can safely import pipeline modules
from pipeline import load_tab
from metrics import calc_metrics
from audit import run_checksums

# ─── 2. Streamlit Page Config & Custom CSS ────────────────────────────────────

# Inject Custom CSS for OLED Dark Theme & Table Styling
oled_dark_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Typography & Colors */
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif !important;
        background-color: #050505 !important;
        color: #e0e0e0 !important;
    }

    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #222 !important;
    }

    /* Metric/Text accents */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Radio button / segmented control styling */
    div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: row;
        gap: 15px;
    }

    /* Table Customization */
    /* Remove borders */
    [data-testid="stTable"] table, [data-testid="stTable"] th, [data-testid="stTable"] td, .stDataFrame table, .stDataFrame th, .stDataFrame td {
        border: none !important;
    }

    /* Zebra striping */
    [data-testid="stTable"] tr:nth-child(even), .stDataFrame tr:nth-child(even) {
        background-color: #111111 !important;
    }
    [data-testid="stTable"] tr:nth-child(odd), .stDataFrame tr:nth-child(odd) {
        background-color: #050505 !important;
    }

    /* Header styling & Sticky Header */
    [data-testid="stTable"] th, .stDataFrame th {
        background-color: #1a1a1a !important;
        color: #007bff !important;
        text-transform: uppercase !important;
        font-weight: 700 !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
        padding-top: 12px !important;
        padding-bottom: 12px !important;
    }

    /* Cell padding */
    [data-testid="stTable"] td, .stDataFrame td {
        padding: 10px 15px !important;
    }

    /* Highlight class for negative numbers (assigned via pandas styler) */
    .negative-val {
        color: #ff4b4b !important;
        font-weight: 500 !important;
    }
</style>
"""
st.markdown(oled_dark_css, unsafe_allow_html=True)


# ─── 3. Data Fetching & Caching ───────────────────────────────────────────────

def get_financial_data(ticker: str, period_type: str, sheet: str):
    """Fetch financial data securely, without caching errors."""
    try:
        if sheet == "cstc":
            df = calc_metrics(ticker, period_type)
        else:
            df = load_tab(ticker, period_type, sheet)
        return df
    except Exception as e:
        return None

# Wrap it in cache_data that relies on the arguments, but ONLY caches on success
# Streamlit doesn't natively support conditionally caching. But we can raise an 
# exception and handle it in the UI to prevent caching, OR simply don't cache 
# (Parquet read is sub-second anyway). Since the plan requested 
# "instant switching", let's use a cached wrapper.

@st.cache_data(show_spinner=False, ttl=60) # Adding a TTL of 60 seconds as a failsafe
def _get_cached_financial_data(ticker: str, period_type: str, sheet: str):
    df = get_financial_data(ticker, period_type, sheet)
    if df is None or df.empty:
        # Don't cache empty results indefinitely. A short TTL handles this mostly,
        # but to be completely safe, we could raise an exception.
        raise ValueError("No data")
    return df

def safe_get_financial_data(ticker: str, period_type: str, sheet: str):
    try:
        return _get_cached_financial_data(ticker, period_type, sheet)
    except ValueError:
        return None

@st.cache_data(show_spinner=False, ttl=60)
def get_audit_status(ticker: str, period_type: str):
    """Run CFO Audit Checksums quietly."""
    try:
        cdkt_df = load_tab(ticker, period_type, "cdkt")
        results = run_checksums(cdkt_df)
        if results:
            # We just take the status of the most recent period
            latest_period = list(results.keys())[0]
            return results[latest_period]["status"]
    except Exception:
        pass
    return "UNKNOWN"


# ─── 4. Table Formatting ──────────────────────────────────────────────────────

def format_dataframe(df: pd.DataFrame, n_cols: int):
    """Apply styling: format numbers, indent labels based on level, color negatives."""
    if df is None or df.empty:
        return pd.DataFrame()

    # Determine period columns
    meta_cols = ["field_id", "vn_name", "unit", "level"]
    period_cols = [c for c in df.columns if c not in meta_cols]
    shown_cols = period_cols[:n_cols]

    # Build display dataframe
    display_df = pd.DataFrame()
    
    # 1. Format label column with indents
    # Streamlit dataframe doesn't support leading spaces easily without HTML,
    # but we can try using non-breaking spaces
    def indent_label(row):
        level = int(row.get("level", 0))
        indent = " " * (level * 4)  # 4 spaces per level
        return f"{indent}{row['vn_name']}"

    display_df["Chỉ tiêu"] = df.apply(indent_label, axis=1)

    # 2. Format values
    for col in shown_cols:
        def fmt_val(row_idx):
            val = df.iloc[row_idx][col]
            unit = df.iloc[row_idx].get("unit", "")
            
            if pd.isna(val) or val is None:
                return "—"
            
            try:
                fval = float(val)
            except (ValueError, TypeError):
                return "—"
            
            if unit in ("%", "lần"):
                formatted = f"{fval:,.2f}"
            elif unit == "đồng/cp":
                formatted = f"{fval:,.0f}"
            else:
                # Value is in VND. Convert to Tỷ VNĐ
                if abs(fval) >= 1e9:
                    formatted = f"{fval / 1e9:,.1f}"
                elif abs(fval) >= 1e6:
                    formatted = f"{fval / 1e6:,.2f}M"
                elif fval == 0.0:
                    formatted = "—"
                else:
                    formatted = f"{fval:,.0f}"
            
            return formatted

        display_df[col] = [fmt_val(i) for i in range(len(df))]

    # 3. Apply Styler for negative numbers (Soft Red)
    def color_negative(val):
        if not isinstance(val, str):
            return ""
        # Check if negative, handling formatted strings (e.g. "-1,234.5")
        if val.startswith("-"):
            return "color: #ff4b4b; font-weight: 500;"
        return "color: #e0e0e0;"

    styled_df = display_df.style.applymap(color_negative, subset=shown_cols)
    return styled_df


# ─── 5. UI Layout & Main App ──────────────────────────────────────────────────

def main():
    # Sidebar
    with st.sidebar:
        st.title("🦁 FINSANG")
        st.markdown("*Terminal Viewer V2.0*")
        st.markdown("---")
        
        ticker = st.text_input("Mã Chứng Khoán (Ticker)", value="VHC").upper()
        
        st.markdown("---")
        period_type_map = {"Quý": "quarter", "Năm": "year"}
        period_label = st.radio("Độ phân giải thời gian", options=list(period_type_map.keys()), index=0)
        period_type = period_type_map[period_label]
        
        n_cols = st.slider("Số kỳ hiển thị", min_value=1, max_value=20, value=8)

        st.markdown("---")
        st.caption("🚀 Powered by Streamlit & Finsang Engine")

    # Header section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{ticker}   |  Báo Cáo Tài Chính")
        st.caption(f"Chế độ: **▶ {period_label.upper()}**  ·  Đơn vị: tỷ VNĐ  ·  Hiển thị: {n_cols} kỳ gần nhất")
    
    with col2:
        # Audit Badge
        audit_status = get_audit_status(ticker, period_type)
        if audit_status == "PASS":
            st.success(f"CFO Audit: ✅ PASS")
        elif audit_status == "FAIL":
            st.error(f"CFO Audit: ❌ FAIL")
        elif audit_status == "WARN":
            st.warning(f"CFO Audit: ⚠️ WARN")
        else:
            st.info(f"CFO Audit: N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Cân đối kế toán (CĐKT)", 
        "Kết quả kinh doanh (KQKD)", 
        "Lưu chuyển tiền tệ (LCTT)", 
        "Chỉ số tài chính (CSTC)"
    ])

    sheet_map = {
        tab1: "cdkt",
        tab2: "kqkd",
        tab3: "lctt",
        tab4: "cstc"
    }

    for tab, sheet_id in sheet_map.items():
        with tab:
            with st.spinner(f"Đang tải {sheet_id.upper()}..."):
                raw_df = safe_get_financial_data(ticker, period_type, sheet_id)
                
                if raw_df is None or raw_df.empty:
                    st.error(f"❌ Không tìm thấy dữ liệu `{sheet_id.upper()}` cho mã `{ticker}` (bộ lọc: {period_label}). Vui lòng chạy pipeline trước.")
                else:
                    styled_df = format_dataframe(raw_df, n_cols)
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        hide_index=True,
                    )

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import dateutil.relativedelta as rd

# --- 1. CORE UTILITIES ---
def get_next_dates(ref_ex_str, ref_pay_str, interval_months=3):
    today = datetime.now()
    curr_ex = datetime.strptime(ref_ex_str, '%m/%d/%Y')
    curr_pay = datetime.strptime(ref_pay_str, '%m/%d/%Y')
    # Advance to the future
    while curr_ex <= today:
        curr_ex += rd.relativedelta(months=interval_months)
        curr_pay += rd.relativedelta(months=interval_months)
    return curr_ex.date(), curr_pay.date()

def get_30_360_days(start, end):
    d1 = min(start.day, 30)
    d2 = 30 if (d1 >= 30 and end.day == 31) else end.day
    if start.month == 2 and (start + timedelta(days=1)).month == 3: d1 = 30
    if end.month == 2 and (end + timedelta(days=1)).month == 3: d2 = 30
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1)

# --- 2. FIXED-RATE DATASET (Extracted from Spreadsheet & Search) ---
# Tickers identified as Fixed-Rate (no floating spread/start date)
FIXED_DATA = {
    'NLY-J':  {'coupon': 0.08875, 'yahoo': 'NLY-PJ',  'ref_ex': '03/31/2024', 'ref_pay': '04/30/2024', 'freq': 3},
    'AGNCZ':  {'coupon': 0.08750, 'yahoo': 'AGNCZ',   'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024', 'freq': 3},
    'ARR-C':  {'coupon': 0.07000, 'yahoo': 'ARR-PC',  'ref_ex': '04/15/2024', 'ref_pay': '04/29/2024', 'freq': 1}, # Monthly
    'FBRT-E': {'coupon': 0.07500, 'yahoo': 'FBRT-PE', 'ref_ex': '03/31/2024', 'ref_pay': '04/10/2024', 'freq': 3},
    'RITM-E': {'coupon': 0.08750, 'yahoo': 'RITM-PE', 'ref_ex': '04/01/2024', 'ref_pay': '04/30/2024', 'freq': 3},
    'PMT-C':  {'coupon': 0.06750, 'yahoo': 'PMT-PC',  'ref_ex': '04/15/2024', 'ref_pay': '04/30/2024', 'freq': 3},
    'MFA-B':  {'coupon': 0.07500, 'yahoo': 'MFA-PB',  'ref_ex': '03/03/2024', 'ref_pay': '03/31/2024', 'freq': 3},
    'CIM-A':  {'coupon': 0.08000, 'yahoo': 'CIM-PA',  'ref_ex': '03/01/2024', 'ref_pay': '03/30/2024', 'freq': 3},
    'ADAMZ':  {'coupon': 0.07000, 'yahoo': 'ADAMZ',   'ref_ex': '04/01/2024', 'ref_pay': '04/15/2024', 'freq': 3},
    'MITT-A': {'coupon': 0.08250, 'yahoo': 'MITT-PA', 'ref_ex': '03/31/2024', 'ref_pay': '04/30/2024', 'freq': 3},
    'MITT-B': {'coupon': 0.08000, 'yahoo': 'MITT-PB', 'ref_ex': '03/31/2024', 'ref_pay': '04/30/2024', 'freq': 3}
}

# --- 3. UI SETUP ---
st.set_page_config(page_title="Fixed-Rate Preferred Tracker", layout="wide")
st.title("📊 Fixed-Rate Preferred Securities")

st.markdown(
    f"<p style='font-size: 0.78rem; color: #808495; margin-bottom: 25px;'>"
    f"Note: Prices are retrieved via yfinance. Accrued dividends and clean price yields are calculated based on 30/360 day counts."
    f"</p>", 
    unsafe_allow_html=True
)

# --- 4. DATA PROCESSING ---
today = datetime.now()
rows = []

for ticker, info in FIXED_DATA.items():
    # 1. Fetch Price
    try:
        price = float(yf.Ticker(info['yahoo']).history(period="1d")['Close'].iloc[-1])
    except:
        price = 25.0
    
    # 2. Get Next Dates
    next_ex, next_pay = get_next_dates(info['ref_ex'], info['ref_pay'], info['freq'])
    
    # 3. Calculate Accrued
    prior_ex = next_ex - rd.relativedelta(months=info['freq'])
    days_accrued = get_30_360_days(prior_ex, today.date())
    
    # Yearly div = Coupon * $25
    annual_div = info['coupon'] * 25
    accrued = annual_div * (days_accrued / 360)
    
    # 4. Yield Calculations
    clean_p = price - accrued
    yld = annual_div / clean_p if clean_p > 0 else 0

    rows.append({
        "Ticker": ticker,
        "Coupon": info['coupon'] * 100,
        "Price": price,
        "Accrued": accrued,
        "Full Div Amount": annual_div / (12 / info['freq']),
        "Clean Price": clean_p,
        "Current Yield": yld * 100,
        "Next Ex-Div": next_ex,
        "Next Pay": next_pay
    })

# --- 5. RENDER DASHBOARD ---
st.subheader("Preferred Yields")
df = pd.DataFrame(rows)

st.dataframe(
    df, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Coupon": st.column_config.NumberColumn(format="%.2f%%"),
        "Price": st.column_config.NumberColumn(format="$%.2f"),
        "Accrued": st.column_config.NumberColumn(format="$%.3f"),
        "Full Div Amount": st.column_config.NumberColumn(format="$%.3f", help="Amount paid per cycle (Monthly or Quarterly)"),
        "Clean Price": st.column_config.NumberColumn(format="$%.2f"),
        "Current Yield": st.column_config.NumberColumn(format="%.2f%%"),
        "Next Ex-Div": st.column_config.DateColumn(format="MM/DD/YYYY"),
        "Next Pay": st.column_config.DateColumn(format="MM/DD/YYYY"),
    }
)

st.markdown("<p style='font-size: 0.78rem; color: #808495;'>* Yields calculated using the 'Clean Price' (Price minus Accrued Dividend).</p>", unsafe_allow_html=True)

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

st.set_page_config(page_title="Daily Portfolio Dashboard", layout="wide")
st.title("📈 Daily Portfolio Performance Tracker")

# 1. PORTFOLIO CONFIGURATION
portfolio_shares = {
    'MSFT': 100,
    'NVDA': 2000,
    'GOOG': 1000,
    'AMZN': 400,
    'KLAC': 350,
    'AVGO': 2730,
    'CVX': 400,
    'GEV': 176,
    'CEG': 90,
    'VST': 183,
    'TSM': 50
}

custom_div_start_dates = {'GOOG': '2026-08-01'}

tickers = list(portfolio_shares.keys())
today = datetime.now()
end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')

# 2. FETCH DATA
@st.cache_data(ttl=300)  # Caches data for 5 minutes so it loads fast
def load_data():
    df_all = yf.download(tickers, start="2025-12-31", end=end_date, actions=True, progress=False)
    
    if isinstance(df_all.columns, pd.MultiIndex):
        df_close = df_all['Close'].copy()
        df_divs = df_all['Dividends'].copy()
    else:
        df_close = df_all[['Close']].copy()
        df_divs = df_all[['Dividends']].copy()
        
    return df_close, df_divs

df_close, df_divs = load_data()

latest_date = df_close.index[-1].strftime('%Y-%m-%d')
prev_date = df_close.index[-2].strftime('%Y-%m-%d')

latest_prices = df_close.iloc[-1].round(2)
prev_prices = df_close.iloc[-2].round(2)
year_start_prices = df_close.loc['2025-12-31'].round(2)

divs_ytd = pd.Series(index=tickers, dtype='float64')
for ticker in tickers:
    start_date = custom_div_start_dates.get(ticker, '2026-01-01')
    if ticker in df_divs.columns:
        divs_ytd[ticker] = df_divs[ticker].loc[start_date:].sum()
    else:
        divs_ytd[ticker] = 0.0

df_portfolio = pd.DataFrame({
    'Shares': pd.Series(portfolio_shares),
    'Latest Price': latest_prices,
    'Prev Price': prev_prices,
    'Divs Recd/Share': divs_ytd.round(2)
})

df_portfolio['Position Value ($)'] = df_portfolio['Shares'] * df_portfolio['Latest Price']
df_portfolio['1-Day Change ($)'] = df_portfolio['Shares'] * (df_portfolio['Latest Price'] - df_portfolio['Prev Price'])
df_portfolio['1-Day Change %'] = ((df_portfolio['Latest Price'] - df_portfolio['Prev Price']) / df_portfolio['Prev Price']) * 100

total_val = df_portfolio['Position Value ($)'].sum()
total_change = df_portfolio['1-Day Change ($)'].sum()
pct_change = (total_change / (total_val - total_change)) * 100

# 3. DISPLAY HEADER METRICS
col1, col2, col3 = st.columns(3)
col1.metric("Total Portfolio Value", f"${total_val:,.2f}")
col2.metric("Today's Dollar Change", f"${total_change:+,.2f}", delta=f"{pct_change:+.2f}%")
col3.metric("Data As Of", latest_date)

st.markdown("---")

# 4. DISPLAY HOLDINGS TABLE
st.subheader("Holdings Detail")
st.dataframe(df_portfolio.style.format({
    'Latest Price': '${:,.2f}',
    'Prev Price': '${:,.2f}',
    'Divs Recd/Share': '${:,.2f}',
    'Position Value ($)': '${:,.2f}',
    '1-Day Change ($)': '{:+,.2f}',
    '1-Day Change %': '{:+.2f}%'
}), use_container_width=True)

# 5. DISPLAY BAR CHART
st.subheader("Position Values & Today's Gain/Loss")
fig, ax = plt.subplots(figsize=(12, 5))
colors = ['#2ca02c' if x >= 0 else '#d62728' for x in df_portfolio['1-Day Change ($)']]
bars = ax.bar(df_portfolio.index, df_portfolio['Position Value ($)'], color=colors, alpha=0.85)

ax.ticklabel_format(style='plain', axis='y')
ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))

max_val = df_portfolio['Position Value ($)'].max()
for i, bar in enumerate(bars):
    yval = bar.get_height()
    day_change = df_portfolio['1-Day Change ($)'].iloc[i]
    ax.text(bar.get_x() + bar.get_width()/2, yval + (max_val * 0.02), f"${yval:,.0f}\n({day_change:+,.0f})", ha='center', va='bottom', fontsize=8, fontweight='bold')

ax.set_ylim(0, max_val * 1.20)
plt.ylabel('Current Value ($)')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

st.pyplot(fig)

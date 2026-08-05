import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# ==========================================
# 1. PORTFOLIO CONFIGURATION
# ==========================================
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

custom_div_start_dates = {
    'GOOG': '2026-08-01'
}

tickers = list(portfolio_shares.keys())

today = datetime.now()
end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')

# ==========================================
# 2. FETCH LIVE MARKET DATA
# ==========================================
df_all = yf.download(tickers, start="2025-12-31", end=end_date, actions=True, progress=False)

if isinstance(df_all.columns, pd.MultiIndex):
    df_close = df_all['Close'].copy()
    df_divs = df_all['Dividends'].copy()
else:
    df_close = df_all[['Close']].copy()
    df_divs = df_all[['Dividends']].copy()

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

divs_ytd = divs_ytd.round(2)

df_portfolio = pd.DataFrame({
    'Shares': pd.Series(portfolio_shares),
    'Latest Price': latest_prices,
    'Prev Price': prev_prices,
    'Divs Recd/Share': divs_ytd
})

df_portfolio['Position Value ($)'] = df_portfolio['Shares'] * df_portfolio['Latest Price']
df_portfolio['1-Day Change ($)'] = df_portfolio['Shares'] * (df_portfolio['Latest Price'] - df_portfolio['Prev Price'])
df_portfolio['1-Day Change %'] = ((df_portfolio['Latest Price'] - df_portfolio['Prev Price']) / df_portfolio['Prev Price']) * 100
df_portfolio['YTD Return %'] = (((df_portfolio['Latest Price'] + df_portfolio['Divs Recd/Share']) - year_start_prices) / year_start_prices) * 100

# Calculate Total Portfolio Summary
total_portfolio_value = df_portfolio['Position Value ($)'].sum()
total_daily_change_dollars = df_portfolio['1-Day Change ($)'].sum()
prev_total_value = total_portfolio_value - total_daily_change_dollars
total_daily_change_pct = (total_daily_change_dollars / prev_total_value) * 100

# Format DataFrame for display and file output
df_display = df_portfolio.copy()
df_display['Latest Price'] = df_display['Latest Price'].map('${:,.2f}'.format)
df_display['Prev Price'] = df_display['Prev Price'].map('${:,.2f}'.format)
df_display['Divs Recd/Share'] = df_display['Divs Recd/Share'].map('${:,.2f}'.format)
df_display['Position Value ($)'] = df_display['Position Value ($)'].map('${:,.2f}'.format)
df_display['1-Day Change ($)'] = df_display['1-Day Change ($)'].map('{:+,.2f}'.format)
df_display['1-Day Change %'] = df_display['1-Day Change %'].map('{:+.2f}%'.format)
df_display['YTD Return %'] = df_display['YTD Return %'].map('{:+.2f}%'.format)

# ==========================================
# 3. SAVE SUMMARY TABLE TO TEXT FILE
# ==========================================
summary_text = (
    f"================================================================"
    f" TOTAL PORTFOLIO VALUE:  ${total_portfolio_value:,.2f}\n"
    f" TODAY'S CHANGE:         {total_daily_change_dollars:+,.2f} ({total_daily_change_pct:+.2f}%)\n"
    f" DATA AS OF:             {latest_date} (vs {prev_date})\n"
    f"================================================================"
    f"\n\n{df_display.to_string()}\n"
)

with open("portfolio_summary.txt", "w") as f:
    f.write(summary_text)

print("Saved portfolio_summary.txt successfully.")

# ==========================================
# 4. GENERATE & SAVE CHART IMAGE
# ==========================================
colors = ['#2ca02c' if x >= 0 else '#d62728' for x in df_portfolio['1-Day Change ($)']]

fig, ax = plt.subplots(figsize=(13, 7))
bars = ax.bar(df_portfolio.index, df_portfolio['Position Value ($)'], color=colors, alpha=0.85)

ax.ticklabel_format(style='plain', axis='y')
ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))

max_val = df_portfolio['Position Value ($)'].max()

for i, bar in enumerate(bars):
    yval = bar.get_height()
    day_change = df_portfolio['1-Day Change ($)'].iloc[i]
    label = f"${yval:,.0f}\n({day_change:+,.0f})"
    ax.text(bar.get_x() + bar.get_width()/2, yval + (max_val * 0.02), label, ha='center', va='bottom', fontsize=8, fontweight='bold')

ax.set_ylim(0, max_val * 1.20)

plt.title(f'Portfolio Position Values ($) & Today\'s Gain/Loss (As of {latest_date})', fontsize=12, fontweight='bold')
plt.xlabel('Stock Ticker')
plt.ylabel('Current Value ($)')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

# Save image file to GitHub repository
plt.savefig("latest_portfolio_chart.png", dpi=300)
print("Saved latest_portfolio_chart.png successfully.")

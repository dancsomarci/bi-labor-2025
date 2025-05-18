import pandas as pd
import yfinance as yf

# Configuration
start_date = "2020-01-01"
output_csv = "sp500_daily_prices.csv"
index_ticker = "^GSPC"

# Load tickers
tickers_url = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
tickers_df = pd.read_csv(tickers_url)
tickers_df.to_csv("sp500_tickers.csv", index=False)
tickers = tickers_df["Symbol"].unique().tolist()
tickers.append(index_ticker)

print("📥 Downloading data from Yahoo Finance...")
df = yf.download(tickers, start=start_date, group_by="ticker", auto_adjust=False)

print("🧹 Reshaping data...")
panel = []
for ticker in tickers:
    if ticker not in df.columns.get_level_values(0):
        print(f"⚠️ Missing data for: {ticker}")
        continue
    data = df[ticker].copy()
    data["Ticker"] = ticker
    data = data.reset_index()
    panel.append(data)

df_all = pd.concat(panel, ignore_index=True)
df_all = df_all[["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]]
df_all["Volume"] = df_all["Volume"].fillna(0).astype("int64")

print("📈 Calculating daily returns...")
df_all["Return"] = df_all.groupby("Ticker")["Close"].pct_change(fill_method=None)

df_all.to_csv(output_csv, index=False)
print(
    f"\n✅ Saved enriched dataset to {output_csv} — rows: {df_all.shape[0]}, columns: {df_all.shape[1]}"
)

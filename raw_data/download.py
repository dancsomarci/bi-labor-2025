import pandas as pd
import yfinance as yf

start_date = "2020-01-01"
output_csv = "sp500_daily_prices.csv"
index_ticker = "^GSPC"

tickers_url = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
tickers_df = pd.read_csv(tickers_url)
tickers_df.to_csv("sp500_tickers.csv", index=False)
tickers = tickers_df["Symbol"].unique().tolist()
tickers.append(index_ticker)
df = yf.download(tickers, start=start_date)

df = df.stack(level="Ticker", future_stack=True).reset_index()
df = df[["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]]
df.to_csv(output_csv, index=False)
print(f"\n✅ Saved to {output_csv} — rows: {df.shape[0]}, columns: {df.shape[1]}")

import datetime
import random

import pandas as pd
import pyodbc

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\mssqllocaldb;"
    "DATABASE=AZTVS7;"
    "Trusted_Connection=yes;"
)
INDEX = "^GSPC"
MA_LOOKBACK_DAYS = 22  # Extra days for moving averages


def simulate_forecast():
    return random.random()


conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()
cursor.execute(
    """
    SELECT MAX(date) FROM index_predictions
    """
)
last_pred_date = cursor.fetchone()[0]
print(f"Last prediction date: {last_pred_date}")
if last_pred_date is None:
    last_pred_date = datetime.date(1900, 1, 1)


query = """
SELECT [id], [date], [close]
FROM [daily_prices]
WHERE [ticker] = ?
  AND [date] >= DATEADD(DAY, -?, ?)
ORDER BY [date]
"""
df = pd.read_sql(query, conn, params=[INDEX, MA_LOOKBACK_DAYS, last_pred_date])
if df.empty:
    raise ValueError("Not enough data to compute forecasts.")

# --- Compute Moving Averages (optional) ---
df["MA_5"] = df["close"].rolling(window=5).mean().fillna(0.0)
df["MA_21"] = df["close"].rolling(window=21).mean().fillna(0.0)
df = df[df["date"] > last_pred_date]  # drop extra rows to avoid reuploading

rows_to_insert = []
for today in df.iterrows():
    rows_to_insert.append(
        (
            today["id"],
            today["date"],
            simulate_forecast(),
            simulate_forecast(),
            simulate_forecast(),
        )
    )

insert_query = """
INSERT INTO index_predictions (
    [daily_price_id], [date],
    [pred_1d], [pred_5d], [pred_21d]
) VALUES (?, ?, ?, ?, ?)
"""


def to_python_native(val):
    if pd.isna(val):
        return None
    if hasattr(val, "item"):
        return val.item()
    return val


params_list = [
    tuple(
        to_python_native(row[col])
        for col in [
            "fact_id",
            "date",
            "pred_1d",
            "pred_5d",
            "pred_21d",
        ]
    )
    for row in rows_to_insert
]
cursor.executemany(insert_query, params_list)

conn.commit()
cursor.close()
conn.close()

print(f"{len(rows_to_insert)} prediction rows inserted.")

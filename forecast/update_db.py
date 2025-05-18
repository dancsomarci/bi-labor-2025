import datetime
import random
import warnings

import pandas as pd
import pyodbc

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\\mssqllocaldb;"
    "DATABASE=AZTVS7;"
    "Trusted_Connection=yes;"
)
INDEX = "^GSPC"
MA_LOOKBACK_DAYS = 22


def simulate_forecast(df: pd.DataFrame) -> list[tuple]:
    return [
        (
            row["id"],
            row["date"],
            random.random(),  # TODO call model
            random.random(),
            random.random(),
        )
        for _, row in df.iterrows()
    ]


def get_last_prediction_date(conn) -> datetime.date:
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(date) FROM index_predictions")
        result = cursor.fetchone()[0]
        return result or datetime.date(1900, 1, 1)


def fetch_price_data(conn, last_date: datetime.date) -> pd.DataFrame:
    query = """
    SELECT [id], [date], [close]
    FROM [daily_prices]
    WHERE [ticker] = ?
      AND [date] >= DATEADD(DAY, -?, ?)
    ORDER BY [date]
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        df = pd.read_sql(query, conn, params=[INDEX, MA_LOOKBACK_DAYS, last_date])
    return df


def compute_features(df, last_date: datetime.date) -> pd.DataFrame:
    df["MA_5"] = df["close"].rolling(window=5).mean().fillna(0.0)
    df["MA_21"] = df["close"].rolling(window=21).mean().fillna(0.0)
    return df[df["date"] > last_date]


def insert_predictions(conn, params: list[tuple]) -> int:
    insert_query = """
    INSERT INTO index_predictions (
        [daily_price_id], [date],
        [pred_1d], [pred_5d], [pred_21d]
    ) VALUES (?, ?, ?, ?, ?)
    """
    with conn.cursor() as cursor:
        cursor.executemany(insert_query, params)
    conn.commit()
    return len(params)


def main():
    with pyodbc.connect(CONN_STR) as conn:
        last_date = get_last_prediction_date(conn)
        print(f"Last prediction date: {last_date}")
        df = fetch_price_data(conn, last_date)
        df = compute_features(df, last_date)
        if df.empty:
            print("No new forecasts to be made.")
            return
        preds = simulate_forecast(df)
        inserted = insert_predictions(conn, preds)
        print(f"{inserted} prediction rows inserted.")


if __name__ == "__main__":
    main()
    input("Press Enter to exit...")

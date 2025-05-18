import datetime
import pickle
import warnings

import numpy as np
import pandas as pd
import pyodbc
from tensorflow.keras.models import load_model

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\\mssqllocaldb;"
    "DATABASE=AZTVS7;"
    "Trusted_Connection=yes;"
)
INDEX = "^GSPC"
SEQ_LEN = 10
LOOKBACK_DAYS = 22 + SEQ_LEN


def process_xy(raw_x: np.array, lookback: int) -> np.array:
    X = np.empty(
        shape=(raw_x.shape[0] - lookback, lookback, raw_x.shape[1]), dtype=np.float32
    )
    target_index = 0
    for i in range(lookback, raw_x.shape[0]):
        X[target_index] = raw_x[i - lookback : i]
        target_index += 1
    return X.copy()


def simulate_forecast(df: pd.DataFrame) -> list[tuple]:
    data = df.drop(columns=["id", "date"])

    with open("scaler_input.pkl", "rb") as f:
        scaler_input = pickle.load(f)
    with open("scaler_output.pkl", "rb") as f:
        scaler_output = pickle.load(f)

    scaled_data = scaler_input.transform(data)
    x = process_xy(scaled_data, lookback=SEQ_LEN)

    model_1day = load_model("best_model_1day.keras")
    model_5day = load_model("best_model_5day.keras")
    model_21day = load_model("best_model_21day.keras")

    day1_preds = scaler_output.inverse_transform(model_1day.predict(x))
    day5_preds = scaler_output.inverse_transform(model_5day.predict(x))
    day21_preds = scaler_output.inverse_transform(model_21day.predict(x))

    df = df.iloc[SEQ_LEN:].copy()

    df["pred_1d"] = day1_preds.flatten()
    df["pred_5d"] = day5_preds.flatten()
    df["pred_21d"] = day21_preds.flatten()

    df = df.dropna(subset=["pred_1d", "pred_5d", "pred_21d"])

    return [
        (
            row["id"],
            row["date"],
            row["pred_1d"],
            row["pred_5d"],
            row["pred_21d"],
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
    SELECT [id], [date], [open], [high], [low], [close], [volume], [return]
    FROM [daily_prices]
    WHERE [ticker] = ?
      AND [date] >= DATEADD(DAY, -?, ?)
    ORDER BY [date]
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        df = pd.read_sql(query, conn, params=[INDEX, LOOKBACK_DAYS, last_date])
    return df


def compute_features(df, last_date: datetime.date) -> pd.DataFrame:
    df["_date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date")

    df = df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "return": "Return",
        }
    )

    df["Quarter"] = df["_date"].dt.quarter
    df["Month"] = df["_date"].dt.month
    df["Quarter.X"], df["Quarter.Y"] = np.sin(2 * np.pi * df["Quarter"] / 4), np.cos(
        2 * np.pi * df["Quarter"] / 4
    )
    df["Month.X"], df["Month.Y"] = np.sin(2 * np.pi * df["Month"] / 12), np.cos(
        2 * np.pi * df["Month"] / 12
    )
    df["Year.X"], df["Year.Y"] = np.sin(
        2 * np.pi * df["_date"].dt.day_of_year / 365
    ), np.cos(2 * np.pi * df["_date"].dt.day_of_year / 365)

    df["MA_5"] = df["Close"].rolling(5).mean()
    df["MA_21"] = df["Close"].rolling(21).mean()
    df["Volatility_5"] = df["Close"].rolling(5).std()
    df["Volatility_21"] = df["Close"].rolling(21).std()
    df["Lag_1"] = df["Close"].shift(1)
    df["Lag_5"] = df["Close"].shift(5)
    df["Lag_21"] = df["Close"].shift(21)

    df = df.drop(["_date", "Quarter", "Month"], axis=1)
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

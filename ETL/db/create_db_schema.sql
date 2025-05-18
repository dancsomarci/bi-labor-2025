CREATE TABLE tickers (
    [id] INT IDENTITY(1,1) PRIMARY KEY,
    [ticker] VARCHAR(50),
    [name] VARCHAR(255),
    [sector] VARCHAR(255),
    [state] VARCHAR(255),
    [founded] INT
);

CREATE TABLE daily_prices (
    [id] INT IDENTITY(1,1) PRIMARY KEY,
    [date] DATE NOT NULL,
    [ticker_id] INT,
    [ticker] VARCHAR(50),
    [open] FLOAT,
    [high] FLOAT,
    [low] FLOAT,
    [close] FLOAT,
    [volume] BIGINT,
    [return] FLOAT,
);

CREATE TABLE monthly_agg (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ticker_id INT,
    last_trading_day DATE,
    min_open FLOAT,
    max_high FLOAT,
    min_low FLOAT,
    max_close FLOAT,
    total_volume BIGINT,
    cumulative_return FLOAT,
);

CREATE TABLE index_predictions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    daily_price_id INT,
    date DATE NOT NULL,
    pred_1d FLOAT,
    pred_5d FLOAT,
    pred_21d FLOAT,
    real_1d FLOAT,
    real_5d FLOAT,
    real_21d FLOAT,
);

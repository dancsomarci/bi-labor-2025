-- Step 1: Get the latest aggregated date
DECLARE @latest_aggregated_date DATE = (
    SELECT ISNULL(MAX(last_trading_day), '1900-01-01') FROM monthly_agg
);

-- Step 2: Compute the first day of the current month (to avoid partial months)
DECLARE @current_month_start DATE = DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1);

-- Step 3: Insert aggregates for months fully after @latest_aggregated_date and before the current month
INSERT INTO monthly_agg (
  ticker_id,
  last_trading_day,
  min_open,
  max_high,
  min_low,
  max_close,
  total_volume,
  cumulative_return
)
SELECT
  ticker_id,
  MAX([date]) AS last_trading_day,
  MIN([open]) AS min_open,
  MAX([high]) AS max_high,
  MIN([low]) AS min_low,
  MAX([close]) AS max_close,
  SUM([volume]) AS total_volume,
  (MAX([close]) / MIN([open])) - 1 AS cumulative_return
FROM daily_prices
WHERE
  [date] > @latest_aggregated_date AND [date] < @current_month_start
GROUP BY
  ticker_id,
  DATEFROMPARTS(YEAR([date]), MONTH([date]), 1);
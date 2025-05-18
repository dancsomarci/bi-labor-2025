WITH FuturePrices AS (
    SELECT
        id AS daily_price_id,
        [date],
        LEAD([close], 1) OVER (ORDER BY [date]) AS true_1d,
        LEAD([close], 5) OVER (ORDER BY [date]) AS true_5d,
        LEAD([close], 21) OVER (ORDER BY [date]) AS true_21d
    FROM daily_prices
    WHERE ticker_id IS NULL
)
UPDATE [ip]
SET
    [ip].real_1d = fp.true_1d,
    [ip].real_5d = fp.true_5d,
    [ip].real_21d = fp.true_21d
FROM index_predictions [ip]
JOIN FuturePrices fp
    ON [ip].daily_price_id = fp.daily_price_id
WHERE [ip].real_21d is NULL;
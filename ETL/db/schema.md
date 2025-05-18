## DB Schema

[dbdiagram.io](https://dbdiagram.io/d)

```
Table daily_prices {
  id integer [primary key]
  date date
  ticker_id integer [ref: > dim_ticker.id]
  open float
  high float
  low float
  close float
  volume bigint
  return float
}

Table dim_ticker {
  id integer [primary key]
  ticker varchar
  name varchar
  industry varchar
  city varchar
  state varchar
  founded integer
}

Table index_predictions {
  id integer [primary key]
  fact_id integer [ref: > daily_prices.id]
  date date
  
  pred_1d float
  pred_5d float
  pred_21d float

  true_1d float
  true_5d float
  true_21d float
}

Table monthly_agg {
  id integer [primary key]
  ticker_id integer [ref: > dim_ticker.id]
  last_trading_day date
  min_open float
  max_high float
  min_low float
  max_close float
  total_volume bigint
  cumulative_return float // best possible return that month
}
```

# User guide

## Which file should I use?

- **Parquet**: preferred full analytical format for Python, R, DuckDB, Polars, or Arrow.
- **DuckDB**: easiest way to query the release with SQL without loading it all into memory.
- **Stata `.dta`**: latest public snapshot for Stata users.
- **CSV.GZ**: universal exchange format.
- **Excel explorer**: documentation and selected rankings only; it is not the master database because spreadsheet row limits are inappropriate for the historical product-market panel.

## Example question

> Which large and growing destination-product markets have low Bangladesh market share but relatively high trade familiarity?

Filter the latest snapshot for high `destination_market_usd`, positive `market_cagr_5y`, low `bd_market_share`, and then rank using the transparent `market_attractiveness` and `trade_familiarity_index` fields.

## Important distinction

`market_attractiveness` and `trade_familiarity_index` are descriptive screening indices. They are not forecasts. Private model fields such as `entry_probability_3y` are estimated separately and require out-of-time validation.

# Stock Analysis Pipeline Project



## Business Requirements



An MVP of a quantitative stock scanning pipeline to identify high-quality breakout candidates.

* The pipeline scans a specific universe of tickers from yfinance most active 100 stocks

* Focuses on daily price/volume and quarterly fundamental metrics

* Filters out illiquid or poorly structured stocks before calculating scores

* Combines technical momentum, relative strength, volume characteristics, volatility metrics, and growth data into a normalized score

* Applies a broad market filter to adjust risk exposure dynamically

* Generates a single, clearly ranked output table of qualified stock setups

* No interactive visual interface required for the MVP; execution happens via script or command line with flat-file output



## Technical Details



* Implemented as a clean, modular Python codebase

* Native integrations with data providers (e.g., yfinance) to fetch historical prices, volumes, and fundamentals

* No persistence layers or external databases needed; reads from configurable inputs and writes directly to target files

* Heavy reliance on vectorized data operations (such as pandas and numpy) for clean, maintainable logic

* Project scaffolding uses explicit path configurations to organize logic, raw data inputs, and runtime logging



## Project Implementation Flow



### 1. Overall Process

* Start with a list of tickers you want to scan.

* Download daily price and volume history for all those tickers plus SPY and the sector ETFs you care about (XLK, SOXX, IGV, etc.) for at least the past 252 trading days.

* Download quarterly fundamentals for each stock (revenue and EPS for at least the last 4–12 quarters).

* For each stock:

    * Apply hard eligibility filters.

    * If it passes, compute each scoring component.

    * Combine component scores into a raw total.

    * Normalize that raw total to a 0–100 score.

    * Apply a market regime multiplier based on SPY.

    * Assign a tier (Tier 1/2/3).

* Collect all results into a table, sort by score, and export to CSV.



### 2. Eligibility Checks

For each stock, do the following checks using the most recent data:

* **Trading history length**: If the stock has fewer than ~200 trading days of history, skip it.

* **Liquidity**: Calculate the average volume over the last 20 days. If that average is below 750,000 shares, skip it.

* **Price**: If the latest closing price is below 10 dollars, skip it.

* **Trend alignment**: Calculate the 50-day, 150-day, and 200-day moving averages of the closing price. Require that:

    * The current price is above the 50-day average.

    * The 50-day average is above the 150-day average.

    * The 150-day average is above the 200-day average.

    * The 200-day average today is higher than it was about 30 trading days ago.

    * If any of these fail, skip the stock.

* **Position in its 52-week range**: Find the highest high and lowest low over the last 252 trading days. Require that:

    * The current price is at least 30% above the 52-week low.

    * The current price is no more than 25% below the 52-week high.

    * If either fails, skip the stock.



Only stocks that pass all of these checks move on to the scoring stage.



### 3. Market Regime

Using SPY:

* Use SPY’s daily close series.

* Compute SPY’s 50-day and 200-day moving averages.

* Compute SPY’s 63-day return (roughly 3 months).

* Find how far SPY is from its 52-week high (in percent).



Classify the regime and assign a multiplier:

* **Strong regime**: SPY is above its 50-day average, the 50-day average is above the 200-day average, and the 63-day return is positive. → Multiplier 1.0.

* **Weak regime**: SPY is below its 200-day average, or SPY is more than 10% below its 52-week high. → Multiplier 0.6.

* **Neutral regime**: Map any state not fitting Strong or Weak. → Multiplier 0.85.



You’ll apply this multiplier to each stock’s normalized score at the end.



### 4. Relative Strength vs Market and Sector

Compute relative strength values for all stocks, then convert them to percentiles.



* **RS vs SPY (market)**: Compute 63-day and 126-day returns for the stock and SPY. Divide the stock’s return by SPY’s return for each horizon. Average the 63-day and 126-day ratios. Rank these values across all stocks, convert to percentiles (0 to 1), and multiply by 20 to get a score (0–20 points).

* **RS vs sector**: Identify its sector ETF (e.g., XLK, SOXX). Compute 63-day and 126-day returns for both stock and sector ETF. Divide stock returns by sector returns and average them. Rank values within each specific sector group, convert to percentiles (0 to 1), and multiply by 15 to get a score (0–15 points).



### 5. Volume and Accumulation

* **Up/Down volume accumulation**: Look at the last 20 trading days. Sum the volume on up days (close > previous close) to get total up volume. Sum the volume on down days (close < previous close) to get total down volume. Divide up volume by down volume to get an accumulation ratio. Rank across the universe, convert to percentiles (0 to 1), and multiply by 12 to get a score (0–12 points).

* **Relative volume (short-term demand)**: Compute the average volume over the last 20 days. Compute 1-day relative volume (today volume / 20-day average) and 3-day relative volume (3-day average volume / 20-day average). Take the larger of the two metrics.

    * Relative volume >= 2.0 → 8 points

    * Relative volume between 1.5 and 2.0 → 5 points

    * Relative volume between 1.2 and 1.5 → 3 points

    * Otherwise → 0 points



### 6. Volatility Compression and Pattern Quality

* **Bollinger Band width compression**: Compute a 20-day simple moving average and a 20-day standard deviation of the closing price. Upper/lower bands use 2 standard deviations. Band width = (upper - lower) / moving average. Take the last 120 days of band width values and find the percentile ranking of today's width.

    * Today's percentile >= 0.5 → 0 points

    * Today's percentile < 0.5 → Map 0 percentile to 15 points and 0.5 percentile to 0 points linearly in between.

* **Pattern quality checklist**: Assign 1 point for each condition that is true (0 to 5 points max):

    * Current price is within 10% of its 52-week high.

    * Last 20 trading days trade within a band of 15% or less from low to high.

    * Most recent swing low in the base is higher than the prior swing low.

    * 10-day moving average is above the 20-day moving average, and both are rising compared with a few days ago.

    * Within the last 20 days, the stock has not fallen more than 12% below its 52-week high.



### 7. Proximity to Resistance

* Find the highest high over the last 50 days and the last 65 days. Take the larger of those two as your resistance level.

* Compute the distance between resistance and the current close as a percentage of resistance.

    * Distance <= 3% → 5 points

    * Distance between 3% and 8% → 3 points

    * Distance > 8% → 0 points



### 8. Fundamentals: Revenue and EPS

* **Revenue growth**: Find year-over-year percentage growth for the most recent quarter (or average the most recent 2 quarters for stability).

    * Growth >= 40% → 15 points

    * Growth between 25% and 40% → 12 points

    * Growth between 15% and 25% → 8 points

    * Growth between 5% and 15% → 4 points

    * Growth < 5% or negative → 0 points

* **EPS growth**: Get the YoY EPS growth percentage for the most recent quarter. Combine it with a 3-year EPS compound annual growth rate using a weighted average heavily favoring the latest quarter.

    * Combined metric >= 50% → 15 points

    * Combined metric between 30% and 50% → 12 points

    * Combined metric between 15% and 30% → 8 points

    * Combined metric between 0% and 15% → 4 points

    * Combined metric negative → 0 points



### 9. Total Score, Normalization, and Tiering

Add up all component scores (Maximum possible raw score is 120). Normalize by dividing the raw score by 120 and multiplying by 100 to yield a 0–100 score. Apply the market regime multiplier to get the final adjusted score.



Assign tiers based on the metrics:

* **Tier 1 (breakout ready)**:

    * Normalized score is 80 or higher.

    * Final adjusted score is 70 or higher.

    * Compression score is at least 8.

    * Either accumulation score is at least 8 or relative-volume score is at least 5.

* **Tier 2 (high-quality watchlist)**:

    * Normalized score is between 65 and 79, OR

    * Normalized score is 80+ but compression/volume conditions for Tier 1 are not fully met.

* **Tier 3 (ignore for now)**:

    * Normalized score is below 65.



### 10. Final Output

* For every stock, store: Ticker, each component score, raw score, normalized score, final adjusted score, and tier.

* Put records into a table and sort by final adjusted score descending. Use RS vs market score and accumulation score as descending tie-breakers.

* Save the resulting table to a CSV file (e.g., breakout_scan_results.csv).



## Strategy



* Write plan with success criteria for each phase to be checked off. Include project scaffolding, including .gitignore, and rigorous unit testing.

* Execute the plan ensuring all criteria are met

* Carry out extensive integration testing, fixing defects

* Only complete when the MVP is finished and tested, with the engine ready for execution



## Coding Standards



* Use latest versions of libraries and idiomatic approaches as of today

* Keep it simple - NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. No extra features - focus on simplicity.

* Be concise. Keep README minimal. IMPORTANT: no emojis ever

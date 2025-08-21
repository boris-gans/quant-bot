
## Components of the Bot

* **`exchange_wrapper.py`** → Uses `ccxt` to connect to whatever exchange you configure (Kraken, Coinbase, OKX, etc.). Handles all **real-time API calls** (fetch data, send orders, balances).
* **`data_handler.py`** → Converts raw OHLCV from the exchange into a clean `pandas` DataFrame. This is your **data ingestion pipeline**.
* **`strategies/*.py`** → Apply logic (MA crossover, RSI, etc.) to produce **signals**.
* **`trader.py`** → Takes a signal (+ risk rules later) and decides whether to place an order via the exchange wrapper.
* **`backtester.py`** (future module) → Runs strategies on historical data offline, without touching an exchange.
* **`main.py`** → Orchestrates the whole flow: fetch data → generate signal → execute trade.

---

## Paper Trading on Kraken (simulated real-time futures trading)

* **Kraken** → Provides a sandbox environment for futures (testnet API). You can place “fake” orders that execute against simulated order books.
* **ccxt** → Acts as the **middleman** between your bot and Kraken’s API. All function calls like `fetch_ohlcv()` or `create_order()` go through `ccxt`.
* **Flow**:

  1. `main.py` runs.
  2. `exchange_wrapper` calls `ccxt.kraken` with **sandbox credentials**.
  3. `data_handler` pulls OHLCV candles from Kraken Testnet.
  4. `strategy` generates signals (e.g., MA crossover).
  5. `trader` sends buy/sell to Kraken Testnet via `ccxt`.
  6. Trades settle in Kraken’s paper account (no real money).

**Scripts used**: `main.py`, `exchange_wrapper.py`, `data_handler.py`, `moving_average.py`, `trader.py`
**Kraken role**: Paper-trade execution + live price data.
**ccxt role**: Standardized API client so your code doesn’t care it’s Kraken specifically.

---

## Backtesting on Historical Data from Kraken

* **Kraken** → Just a **data provider** here (historical OHLCV).
* **ccxt** → Still the middleman, but now you’re using only `fetch_ohlcv()` for a long range of historical data.
* **Flow**:

  1. `backtester.py` requests OHLCV via `ccxt.kraken`.
  2. `data_handler` structures it into a `pandas` DataFrame.
  3. Strategy module (`moving_average.py`) generates buy/sell signals across the full historical dataset.
  4. `backtester.py` simulates trades using those signals (entry/exit logic, PnL calc, slippage modeling).
  5. No orders are sent to Kraken. Everything happens **locally in your code**.

**Scripts used**: `backtester.py`, `data_handler.py`, `moving_average.py` (not `trader.py` because we’re simulating).
**Kraken role**: Historical data source.
**ccxt role**: Interface for pulling that data.

---

## Using a Different Exchange (not Kraken)

* **Different Exchange** (e.g., Coinbase, OKX, Binance) → Provides market data + execution, real or paper.
* **ccxt** → This is where ccxt shines. You just change `EXCHANGE = "coinbase"` in `settings.py`, and the rest of your code runs the same.
* **Flow**:

  1. `main.py` runs.
  2. `exchange_wrapper` instantiates `ccxt.coinbase` instead of `ccxt.kraken`.
  3. `data_handler` fetches data from Coinbase.
  4. Strategy generates signals.
  5. Trader sends orders via Coinbase API (through ccxt).

**Scripts used**: Same as scenario 1 (`main.py`, `exchange_wrapper.py`, etc.).
**Kraken role**: None — it’s replaced by another exchange.
**ccxt role**: Abstracts away exchange differences so your bot code doesn’t change.

---

# Database Layout

Using either Postgres or SQLAlchemy

### Schema: `market_data`

* `ohlcv`

  * id (PK)
  * exchange (e.g., "kraken")
  * symbol (e.g., "BTC/USDT")
  * timeframe (e.g., "1h")
  * timestamp (UTC)
  * open, high, low, close, volume

---

### Schema: `trading_logs`

* `signals`

  * id (PK)
  * timestamp
  * symbol
  * signal (buy/sell/hold)
  * reasoning (text, e.g., “short MA > long MA”)
  * indicators (JSON, e.g., `{"short_ma": 30000, "long_ma": 29500}`)

* `orders`

  * id (PK)
  * timestamp
  * exchange\_order\_id
  * symbol
  * side (buy/sell)
  * size
  * price
  * status (submitted, filled, rejected)
  * pnl (nullable until closed)

---

## Where This Fits in The Bot

1. **Data ingestion** (`data_handler.py`)

   * Fetches OHLCV from Kraken (via `ccxt`).
   * Stores it in `market_data.ohlcv`.

2. **Signal generation** (`strategies/*.py`)

   * Strategy computes signals and reasoning.
   * Logs signal → `trading_logs.signals`.

3. **Execution** (`trader.py`)

   * Places order on Kraken paper trading.
   * Logs order → `trading_logs.orders`.


---

# Overview

* **Paper Trading** → Kraken (testnet) + ccxt = execution & data, `trader.py` active.
* **Backtesting** → Kraken (historical OHLCV) + ccxt = data only, `backtester.py` active, no orders.
* **Other Exchanges** → ccxt swaps the backend (Coinbase, OKX…), same bot flow.
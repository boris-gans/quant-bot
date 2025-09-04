from exchange.exchange_wrapper import ExchangeWrapper
from data.data_handler import DataHandler
from strategies.moving_average import MovingAverageStrategy
from trader.trader import Trader
from config.settings import SYMBOL, TIMEFRAME, DATABASE_URL
from utils.logger import Logger
import sys
import pandas as pd
import time


def initialize_database(data_handler, exchange, log):
    """
    Initialization pipeline:
    1. Get instruments
    2. Get instrument status
    3. Get tickers
    4. Get trades
    5. Get order books
    """
    log.info("Starting database initialization...")
    return #safety to not clear db

    # 1. Instruments
    try:
        instruments = exchange.get_instruments()
        if not instruments or "instruments" not in instruments:
            log.error("No instruments returned by exchange")
            sys.exit(1)  # Stop early
        data_handler.init_instruments(instruments["instruments"])
        log.info(f"Saved {len(instruments['instruments'])} instruments")
    except Exception as e:
        log.exception(f"Failed to save instruments: {e}")
        sys.exit(1)

    # 2. Instrument status list
    try:
        # all instruments
        status = exchange.get_instrument_status_list()

        # single instrument
        # status = exchange.get_instrument_status('PI_XBTUSD')

        data_handler.save_instrument_status(status)
    except Exception as e:
        log.warning(f"Failed to fetch statuses: {e}")


    # 3. Tickers
    # All instruments
    try:
        ticker = exchange.get_ticker_list()
        data_handler.save_tickers(ticker)
    except Exception as e:
        log.warning(f"Failed to fetch and save tickers: {e}")

    # 4. Trades
    # All instruments
    for inst in instruments["instruments"]:
        symbol = inst.get("symbol")
        try:
            trades = exchange.get_trade_history(symbol)
            data_handler.save_trade_history(symbol, trades)
        except Exception as e:
            log.warning(f"Failed to fetch trades for {symbol}: {e}")
            continue

    # Single instrument
    # try:
    #     symbol = 'PI_XBTUSD'
    #     trades = exchange.get_trade_history(symbol)
    #     data_handler.save_trade_history(symbol, trades)
    # except Exception as e:
    #     log.warning(f"Failed to fetch trades for {symbol}: {e}")
    

    # 5. Order books
    # All instruments
    for inst in instruments["instruments"]:
        symbol = inst.get("symbol")
        try:
            order_book = exchange.get_order_book(symbol)
            data_handler.save_order_book(symbol, order_book)
        except Exception as e:
            log.warning(f"Failed to fetch order book for {symbol}: {e}")
            continue

    # Single instrument
    # try:
    #     symbol = 'PI_XBTUSD'
    #     order_book = exchange.get_order_book(symbol)
    #     data_handler.save_order_book(symbol, order_book)
    # except Exception as e:
    #     log.warning(f"Failed to fetch trades for {symbol}: {e}")

    log.info("Database initialization completed successfully.")

def live_trading(data_handler, exchange, trader, log):
    # smarter to concurently call each api or in-line?
    """
    Live trading polling: Refresh only neccecesary data, minmize latency
    1. Instrument status: poll frequently for dislocations / volatility
    2. Tickers: poll frequently for live prices, funding rates, etc.
    3. Order books: poll less frequently (unless depth is needed); overwrite each time
    4. Trades: poll frequently, only append new ones (time + symbol as uniqueness)
    """
    # fetch all instruments
    try:
        instruments = data_handler.get_instruments() #df
    except Exception as e:
        log.warning(f"Failed to fetch instruments: {e}")

    # 1. Instrument status
    try:
        # all instruments
        status = exchange.get_instrument_status_list()
        data_handler.save_instrument_status(status)
    except Exception as e:
        log.warning(f"Failed to fetch statuses: {e}")


    # 2. Ticker refresh
    try:
        # all tickers
        ticker = exchange.get_ticker_list()
        data_handler.save_tickers(ticker)
    except Exception as e:
        log.warning(f"Failed to fetch and save tickers: {e}")

    # 3/4. Order book + trades refresh
    # can def optimize; don't loop per instrument
    for inst in instruments:
        symbol = inst["symbol"]
        try:
            order_book = exchange.get_order_book(symbol)
            data_handler.save_order_book(symbol, order_book)

            trades = exchange.get_trade_history(symbol)
            data_handler.save_trade_history(symbol, trades)
        except Exception as e:
            log.warning(f"Failed to fetch order book and trades for {symbol}: {e}")
            continue

    # expects keys: time, open, high, low, close, volume

def live_trading_test(data_handler, exchange, trader, log):
    log.info("Starting LT test...")
    # Need last 100 tickers for one symbol (testing)
    # And orderbook (for liquidity check)

    ohlcv_keys = ["lastTime", "open24h", "high24h", "low24h", "last", "vol24h"]
    df = pd.DataFrame(columns=ohlcv_keys)
    window_rsi = 14

    # Fetch a selection of instruments; just get top one for testing
    try:
        symbol = data_handler.get_instruments()[0]["symbol"]
    except Exception as e:
        log.warning(f"Failed to establish symbol: {e}")

    unique_count = 0
    last_timestamp = None
    
    while unique_count < window_rsi:
        if unique_count != 0:
            time.sleep(60) # wait 1 min for tickers to refresh

        try:
            ticker_data = exchange.get_ticker(symbol)['ticker']
            ohclv_data = {k: ticker_data[k] for k in ohlcv_keys if k in ticker_data}

            current_ts = ticker_data.get("lastTime")
            if not current_ts:
                continue
                # skip if no ts
            log.info(f"Ts comp {current_ts}:{last_timestamp}")
            
            if current_ts != last_timestamp:
                last_timestamp = current_ts
                unique_count += 1

                new_row = pd.DataFrame([ohclv_data])
                df = pd.concat([df, new_row], ignore_index=True)

                data_handler.append_ticker(ticker_data, symbol)
                log.info(f"Added new candle {unique_count}/{window_rsi}: {ohclv_data}")
            else:
                log.info("Duplicate candle, waiting for next...")

            # order_data = exchange.get_order_book(symbol)
        except Exception as e:
            log.warning(f"Failed to fetch ticker data for instrument: {e}")

    try:
        trader.momentum(df, symbol, window_rsi)
    except Exception as e:
        log.warning(f"Failed to generate and execute signals for {symbol}: {e}")


def strategy_test(data_handler, trader, log):
        log.info("Starting strat test...")
        # Need last 100 tickers for one symbol (testing)
        # And orderbook (for liquidity check)

        ohlcv_keys = ["lastTime", "open24h", "high24h", "low24h", "last", "vol24h"]
        df = pd.DataFrame(columns=ohlcv_keys)
        window_rsi = 14

        # just get top one for testing
        try:
            symbol = data_handler.get_instruments()[0]["symbol"]
            tickers_list = data_handler.get_tickers(symbol)
        except Exception as e:
            log.warning(f"Failed to establish symbol: {e}")


        for tick in tickers_list:
            ohclv_data = {k: tick[k] for k in ohlcv_keys if k in tick}
            new_row = pd.DataFrame([ohclv_data])
            df = pd.concat([df, new_row])
        log.info(f"Loaded {len(tickers_list)} ticker(s) into memory")


        try:
            trader.momentum(df, symbol, window_rsi)
        except Exception as e:
            log.warning(f"Failed to generate and execute signals for {symbol}: {e}")


def main():
    try:
        # Init logger
        log = Logger().get_logger()

        # Init exchange + data
        exchange = ExchangeWrapper(log)
        data_handler = DataHandler(DATABASE_URL, log)
        trader = Trader(exchange, log)

        # init db
        # initialize_database(data_handler, exchange, log)


        # call every __ min
        # live_trading(data_handler, exchange, trader, log)
        # live_trading_test(data_handler, exchange, trader, log)
        strategy_test(data_handler, trader, log)
    except KeyboardInterrupt:
        log.info(f"\nKeyboard interrupt received. Shutting down...")
    finally:
        log.info("Shutdown")



if __name__ == "__main__":
    main()


# -----------------------------
# DATA COLLECTION PIPELINE

# Initialization: no data in the db or a daily init
# 1. Get instruments
# 2. get instrument status list
# 3. Get tickers
# 4. Get trades --> this will be refreshed often
# 5. Get order book --> this will be refreshed often

# Live trading polling: Refresh only neccecesary data, minmize latency
# 1. Instrument status: poll frequently for dislocations / volatility
# 2. Tickers: poll frequently for live prices, funding rates, etc.
# 3. Order books: poll less frequently (unless depth is needed); overwrite each time
# 4. Trades: poll frequently, only append new ones (time + symbol as uniqueness)

# Historical data collection / backtesting: Build a large dataset for research
# 1. Trades: append all
# 2. Tickers
# 3. Order books: only needed for depth/liquidity analysis
# 4. Instrument status: rarely needed unless simulating trading restrictions
#   loop through all of these per instrument for a massive dataset

# -----------------------------
# DATA FLOW
# api -> exchange_wrapper as JSON
# exchange_wrapper -> main as JSON
# main -> data_handler as JSON
# main -> trader as df




# COMPONENTS
# exchange_wrapper
"""Uses ccxt to connect to whatever exchange is configured in settings.py"""

# data_handler
"""Converts the raw OHLCV (open, high, low, close and volume) into a clean df"""

# strategies/*
"""Apply logic to data to produce signals"""

# trader
"""Takes a signal (+ additional rules) and decides whether to place an order via exchange_wrapper"""

# backtester
"""Runs strategies on historical data offline without exchange"""

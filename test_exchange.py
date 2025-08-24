from exchange.exchange_wrapper import ExchangeWrapper
from utils.logger import Logger
from data.data_handler import DataHandler
from datetime import datetime
from config.settings import SYMBOL, TIMEFRAME, DATABASE_URL


def main():
    # Init logger
    log = Logger().get_logger()

    # Init exchange
    exchange = ExchangeWrapper(log)
    # contract_type = "futures_inverse"
        # all instruments



    handler = DataHandler(DATABASE_URL, log)

    # Call APIs
    log.info("==== TESTING EXCHANGE WRAPPER ====")

    instruments = exchange.get_instruments()
    instrument_status = exchange.get_instrument_status_list()
    instrument_list = instruments.get("instruments", [])
    instrument_status_list = instrument_status.get("instrumentStatus", [])
    if instrument_list:
        log.info(f"Instruments retrieved: {len(instrument_list)} instruments")
        for i, inst in enumerate(instrument_list[:5], start=1):
            log.info(f"Instrument {i}: {inst['symbol']}")
        for i, inst in enumerate(instrument_status_list[:5], start=1):
            log.info(f"Instrument {inst['tradeable']}: {inst['experiencingDislocation']}")

        symbol = instrument_list[0]["symbol"]
    else:
        log.error("Failed to retrieve instruments")

    # trade_history = exchange.get_trade_history(symbol, last_time="1724200000")
    trade_history = exchange.get_trade_history(symbol)
    trade_list = trade_history.get("history", [])
    if trade_list:
        log.info(f"Trade history retrieved: {len(trade_list)} trades")
    else:
        log.error("Failed to retrieve trade history")

    order_book = exchange.get_order_book(symbol)
    order_list = order_book.get("orderBook").get("bids", [])
    if order_list:
        log.info(f"Order book retrieved: {len(order_list)} bids")
    else:
        log.error("Failed to retrieve order book")

    ticker = exchange.get_tickers()
    ticker_list = ticker.get("tickers", [])
    if ticker_list:
        log.info(f"Ticker list retrieved: {len(ticker_list)} tickers")

        # log.info(f"Ticker last price: {ticker.get('last')}, volume: {ticker.get('volume')}")
    else:
        log.error("Failed to retrieve ticker")

    log.info("==== TESTING COMPLETE ====")

if __name__ == "__main__":
    main()
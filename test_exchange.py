from exchange.exchange_wrapper import ExchangeWrapper
from utils.logger import Logger

def main():
    # Init logger
    log = Logger().get_logger()

    # Init exchange
    exchange = ExchangeWrapper(log)
    # symbol = "PI_BTCUSD"

    # Call APIs
    log.info("==== TESTING EXCHANGE WRAPPER ====")

    instruments = exchange.get_instruments()
    instrument_list = instruments.get("instruments", [])
    if instrument_list:
        log.info(f"Instruments retrieved: {len(instrument_list)} instruments")
        for i, inst in enumerate(instrument_list[:5], start=1):
            log.info(f"Instrument {i}: {inst['symbol']}")
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

    ticker = exchange.get_ticker(symbol)
    print(ticker)
    ticker_list = ticker.get("tickers", [])
    if ticker_list:
        log.info(f"Ticker list retrieved: {len(ticker_list)} tickers")

        # log.info(f"Ticker last price: {ticker.get('last')}, volume: {ticker.get('volume')}")
    else:
        log.error("Failed to retrieve ticker")

    log.info("==== TESTING COMPLETE ====")

if __name__ == "__main__":
    main()
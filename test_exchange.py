from exchange.exchange_wrapper import ExchangeWrapper
from utils.logger import Logger

def main():
    # Init logger
    log = Logger().get_logger()

    # Init exchange
    exchange = ExchangeWrapper(log)
    symbol = "PF_BTCUSD"

    # Call APIs
    log.info("==== TESTING EXCHANGE WRAPPER ====")

    trade_history = exchange.get_trade_history(symbol, last_time="1724200000")
    if trade_history:
        log.info(f"Trade history retrieved: {len(trade_history.get('trades', []))} trades")
    else:
        log.error("Failed to retrieve trade history")

    order_book = exchange.get_order_book(symbol)
    if order_book:
        log.info(f"Order book retrieved: {len(order_book.get('bids', []))} bid levels, {len(order_book.get('asks', []))} ask levels")
    else:
        log.error("Failed to retrieve order book")

    ticker = exchange.get_ticker(symbol)
    if ticker:
        log.info(f"Ticker last price: {ticker.get('last')}, volume: {ticker.get('volume')}")
    else:
        log.error("Failed to retrieve ticker")

    log.info("==== TESTING COMPLETE ====")

if __name__ == "__main__":
    main()
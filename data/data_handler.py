import pandas as pd

class DataHandler:
    """Converts the raw OHLCV (open, high, low, close and volume) into a clean df"""

    def __init__(self, exchange_wrapper, logger):
        self.exchange = exchange_wrapper
        self.logger = logger
        self.logger.info("Initialized DataHandler")


    def get_historical_data(self, symbol, timeframe="1h", limit=200):
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp","open","high","low","close","volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
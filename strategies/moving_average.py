import pandas as pd

class MovingAverageStrategy:
    def __init__(self, short_window=10, long_window=30, logger=None):
        self.short_window = short_window
        self.long_window = long_window
        self.logger = logger
        self.logger.info("Initialized MovingAverageStrategy")


    def generate_signals(self, df: pd.DataFrame):
        df["short_ma"] = df["close"].rolling(window=self.short_window).mean()
        df["long_ma"] = df["close"].rolling(window=self.long_window).mean()
        df["signal"] = 0
        df.loc[df["short_ma"] > df["long_ma"], "signal"] = 1
        df.loc[df["short_ma"] < df["long_ma"], "signal"] = -1
        return df
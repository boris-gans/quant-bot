import pandas as pd


class Trader:
    """Takes a signal (+ additional rules) and decides whether to place an order via exchange_wrapper"""

    def __init__(self, exchange_wrapper, logger):
        self.exchange = exchange_wrapper
        self.logger = logger
        self.logger.info("Initialized Trader")

	# 1. Momentum Investing (short-term RSI, MACD, Volume indicators)
	# 	○ Easiest to start: Kraken provides OHLCV (candles), which is enough.
	# 	○ Implement with RSI (oversold/overbought signals) or MACD crossovers.
	# 	○ Good way to learn backtesting and live execution.


    def momentum(self, data, symbol, amount=0.001):
        """
        RSI: Buy if <30 (oversold), sell if >70 (overbought)
        MACD: Buy if line crosses above signal line, vice-versa
        Volume: Used to confirm signals; only if volume is above average
        """
        self.logger.info("Starting Momentum strategy")

        df = pd.DataFrame([data])
        # lastTime, open24h, high24h, low24h, last, vol24h
        df["close"] = df["last"].astype(float)
        df["volume"] = df["vol24h"].astype(float)

        # calc RSI
        window_rsi = 14
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window_rsi).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window_rsi).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        self.logger.info(f"RSI calculated: \n{df["RSI"]}")

        # calc MACD
        short_window = 12
        long_window = 26
        signal_window = 9
        df["EMA_short"] = df["close"].ewm(span=short_window, adjust=False).mean()
        df["EMA_long"] = df["close"].ewm(span=long_window, adjust=False).mean()
        df["MACD"] = df["EMA_short"] - df["EMA_long"]
        df["Signal"] = df["MACD"].ewm(span=signal_window, adjust=False).mean()
        self.logger.info(f"MACD calculated: \n{df["Signal"]}")


        # filter low volume
        df["vol_avg"] = df["volume"].rolling(window=20).mean()

        # Generate signals
        signal = 0  # 1 = buy, -1 = sell, 0 = hold
        latest = df.iloc[-1]


        if latest["RSI"] < 30:
            signal = 1
        elif latest["RSI"] > 70:
            signal = -1

        if latest["MACD"] > latest["Signal"]:
            if signal == 1:  # only confirm buy if MACD supports it
                signal = 1
        elif latest["MACD"] < latest["Signal"]:
            if signal == -1:  # only confirm sell if MACD supports it
                signal = -1

        if latest["volume"] < latest["vol_avg"]:
            signal = 0

        # execute trade using signals
        return self.execute_signal(symbol, signal, amount)



    def execute_signal(self, symbol, signal, amount=0.001):
        if signal == 1:
            print(f"Buying {symbol}...")
            return self.exchange.create_order(symbol, "buy", amount)
        elif signal == -1:
            print(f"Selling {symbol}...")
            return self.exchange.create_order(symbol, "sell", amount)
        else:
            print("No trade signal")
            return None
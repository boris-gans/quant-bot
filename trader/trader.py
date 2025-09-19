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


    def momentum(self, data, symbol, window_rsi=14, amount=1.00):
        """
        RSI: Buy if <30 (oversold), sell if >70 (overbought)
        MACD: Buy if line crosses above signal line, vice-versa
        Volume: Used to confirm signals; only if volume is above average
        """
        self.logger.info(f"Starting Momentum strategy for: {symbol}")
        self.logger.info(f"{data}")

        if len(data) <= window_rsi:
            window_rsi = len(data) - 1
            self.logger.info(f"Too few rows, setting window_rsi to: {window_rsi}")
        window_rsi = 5

        df = pd.DataFrame(data)
        # lastTime, open24h, high24h, low24h, last, vol24h

        df['lastTime'] = pd.to_datetime(df['lastTime'])
        df.set_index('lastTime', inplace=True)

        # fix d-types
        df["close"] = df["last"].astype(float)
        df["volume"] = df["vol24h"].astype(float)

        # resample to 1-minute candles
        candles = df['last'].resample('1T').ohlc()
        candles['volume'] = df['volume'].resample('1T').sum()
        candles.fillna(method="ffill", inplace=True)

        self.logger.info(f"{candles}")
        # 2025-09-04 13:15:00  111064.0  111064.0  111064.0  111064.0  509112.0
        # 2025-09-04 13:16:00  111050.5  111050.5  111050.5  111050.5  510705.0


        # calc RSI
        delta = candles["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window_rsi).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window_rsi).mean()
        rs = gain / loss
        candles["RSI"] = 100 - (100 / (1 + rs))
        self.logger.info(f"RSI calculated: \n{candles["RSI"]}")

        # calc MACD
        short_window = 12
        long_window = 26
        signal_window = 9
        candles["EMA_short"] = candles["close"].ewm(span=short_window, adjust=False).mean()
        candles["EMA_long"] = candles["close"].ewm(span=long_window, adjust=False).mean()
        candles["MACD"] = candles["EMA_short"] - candles["EMA_long"]
        candles["Signal"] = candles["MACD"].ewm(span=signal_window, adjust=False).mean()
        self.logger.info(f"MACD calculated: \n{candles["Signal"]}")


        # filter low volume
        candles["vol_avg"] = candles["volume"].rolling(window=20).mean()

        # Generate signals
        signal = 0  # 1 = buy, -1 = sell, 0 = hold
        latest = candles.iloc[-1]


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



    def execute_signal(self, symbol, signal, amount=1.00):
        if signal == 1:
            print(f"Buying {symbol}...")
            # return self.exchange.create_order(symbol, "buy", amount)
            # params = {
            #     "orderType": "mkt",
            #     "symbol": symbol,
            #     "side": "buy",
            #     "size": amount,
            # }

            endpoint = "/api/auth/v1/api-keys/v3/check"
            params = {}

            # endpoint = "/api/v3/sendorder"
            # params = {
            #     "orderType": "mkt",
            #     "symbol": symbol,
            #     "side": "buy",
            #     "size": amount,
            #     # "limitPrice": limit_price,
            # }

            return self.exchange.private_request(endpoint_path=endpoint, params=params)
 
        elif signal == -1:
            # print(f"Selling {symbol}...")
            # params = {
            #     "orderType": "mkt",
            #     "symbol": symbol,
            #     "side": "buy",
            #     "size": amount,
            # }
            # return self.exchange.private_request(endpoint_path="/sendorder", params=params)
            # return self.exchange.create_order(symbol, "sell", amount)
            print(signal)
        else:
            print("No trade signal")
            return None
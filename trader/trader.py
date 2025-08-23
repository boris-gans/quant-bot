class Trader:
    """Takes a signal (+ additional rules) and decides whether to place an order via exchange_wrapper"""

    def __init__(self, exchange_wrapper, logger):
        self.exchange = exchange_wrapper
        self.logger = logger
        self.logger.info("Initialized Trader")

    def execute_signal(self, symbol, signal, amount=0.001):
        if signal == 1:
            print("Buying...")
            return self.exchange.create_order(symbol, "buy", amount)
        elif signal == -1:
            print("Selling...")
            return self.exchange.create_order(symbol, "sell", amount)
        else:
            print("No trade signal")
            return None
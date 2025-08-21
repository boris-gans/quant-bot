import ccxt
from config.settings import KRAKEN_API_KEY, KRAKEN_API_SECRET, EXCHANGE

class ExchangeWrapper:
    """Uses ccxt to connect to whatever exchange is configured in settings.py"""

    def __init__(self, exchange_name=EXCHANGE):
        self.exchange_name = exchange_name
        self.exchange = self._init_exchange()

    def _init_exchange(self):
        exchange_class = getattr(ccxt, self.exchange_name)
        return exchange_class({
            "apiKey": KRAKEN_API_KEY,
            "secret": KRAKEN_API_SECRET,
            "enableRateLimit": True
        })

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=100):
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def create_order(self, symbol, side, amount, order_type="market", price=None):
        return self.exchange.create_order(symbol, order_type, side, amount, price)

    def get_balance(self):
        return self.exchange.fetch_balance()
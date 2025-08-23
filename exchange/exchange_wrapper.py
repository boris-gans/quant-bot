import ccxt
import requests
from config.settings import KRAKEN_API_KEY, KRAKEN_API_SECRET, EXCHANGE

# kraken derivatives (sandbox) api docs: https://docs.kraken.com/api/docs/futures-api/trading/market-data


class ExchangeWrapper:
    """Unified exchange wrapper for Kraken Futures (and others via ccxt)."""

    BASE_URL = "https://futures.kraken.com/derivatives/api/v3"  # Market Data API root

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

    # -----------------------
    # Generic ccxt methods
    # -----------------------

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=100):
        """Get OHLCV candles (via ccxt)."""
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def create_order(self, symbol, side, amount, order_type="market", price=None):
        """Place an order (via ccxt)."""
        return self.exchange.create_order(symbol, order_type, side, amount, price)

    def get_balance(self):
        """Fetch account balance (via ccxt)."""
        return self.exchange.fetch_balance()

    # -----------------------
    # Kraken Futures–specific REST calls
    # -----------------------

    def get_trade_history(self, symbol, last_time=None):
        """Completed trades for a symbol (useful for backtests, slippage models)."""
        endpoint = f"{self.BASE_URL}/history"
        params = {"symbol": symbol}
        if last_time:
            params["lastTime"] = last_time
        return requests.get(endpoint, params=params).json()

    def get_order_book(self, symbol):
        """Full snapshot of bids/asks (depth, imbalance, liquidity)."""
        endpoint = f"{self.BASE_URL}/orderbook"
        return requests.get(endpoint, params={"symbol": symbol}).json()

    def get_tickers(self):
        """Market data for ALL contracts + indices (broad monitoring)."""
        endpoint = f"{self.BASE_URL}/tickers"
        return requests.get(endpoint).json()

    def get_ticker(self, symbol):
        """Market data for a single contract/index (lighter request)."""
        endpoint = f"{self.BASE_URL}/ticker"
        return requests.get(endpoint, params={"symbol": symbol}).json()

    def get_instruments(self):
        """Static metadata about all contracts (tick size, expiry, leverage)."""
        endpoint = f"{self.BASE_URL}/instruments"
        return requests.get(endpoint).json()

    def get_instrument_status_list(self):
        """Market health for all instruments (halts, dislocations, volatility flags)."""
        endpoint = f"{self.BASE_URL}/instruments/status"
        return requests.get(endpoint).json()

    def get_instrument_status(self, symbol):
        """Market health for one instrument (lighter request)."""
        endpoint = f"{self.BASE_URL}/instruments/{symbol}/status"
        return requests.get(endpoint).json()

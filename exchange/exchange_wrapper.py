import ccxt
import requests
import base64
import hashlib
import hmac
import time
from config.settings import KRAKEN_API_KEY, KRAKEN_API_SECRET, EXCHANGE


# kraken derivatives (sandbox) api docs: https://docs.kraken.com/api/docs/futures-api/trading/market-data

# no demo-futures support in ccxt, only krakenfutures
# need to create a custom function to generate auth strings


class ExchangeWrapper:
    """Unified exchange wrapper for Kraken Futures (and others via ccxt)."""

    BASE_URL = "https://demo-futures.kraken.com/derivatives/api/v3"  # Market Data API root

    def __init__(self, logger, exchange_name=EXCHANGE):
        self.exchange_name = exchange_name
        self.exchange = self._init_exchange()
        self.logger = logger
        self.logger.info(f"Initialized ExchangeWrapper for exchange {self.exchange_name}")

    def _init_exchange(self):
        exchange_class = getattr(ccxt, self.exchange_name)
        return exchange_class({
            "apiKey": KRAKEN_API_KEY,
            "secret": KRAKEN_API_SECRET,
            "enableRateLimit": True,
        })
    

    # custom helper for demo-kraken (paper trading only)
    def _get_authent(self, post_data, nonce, endpoint_path):
        """Generate the Kraken Futures authent header."""

        message = post_data + nonce + endpoint_path
        sha256_hash = hashlib.sha256(message.encode("utf-8")).digest()
        secret_bytes = base64.b64decode(KRAKEN_API_SECRET)
        hmac512 = hmac.new(secret_bytes, sha256_hash, hashlib.sha512).digest()

        return base64.b64encode(hmac512).decode()


# see: https://github.com/CryptoFacilities/REST-v3-Python/blob/master/cfRestApiV3.py#L32
    def private_request(self, endpoint_path, params=None):
        """Send private request to Kraken Futures API."""
        if params is None:
            params = {}


        nonce = str(int(time.time() * 1000))
        post_data = "&".join(f"{k}={v}" for k, v in params.items()) if params else ""
        authent = self._get_authent(post_data, nonce, endpoint_path)

        url = f"{self.BASE_URL}{endpoint_path}"

        headers = {
            "APIKey": KRAKEN_API_KEY,
            "Authent": authent,
            "Nonce": nonce,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        self.logger.info(f"Requesting {endpoint_path} with url: \n{url} \nHeaders:\n{headers}")

        response = requests.post(url, headers=headers, data=post_data)

        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Request failed [{response.status_code}]: {response.text}")
            response.raise_for_status()



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
        if last_time:
            params = {"symbol": symbol, "lastTime": last_time}
            self.logger.info(f"Fetching trade history for {symbol} since {last_time}")
        else:
            params = {"symbol": symbol}
            self.logger.info(f"Fetching trade history for {symbol}")

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.exception(f"Failed to fetch trade history for {symbol}: {e}")
            return None

    def get_order_book(self, symbol):
        """Full snapshot of bids/asks (depth, imbalance, liquidity)."""
        if not symbol:
            self.logger.error("symbol parameter is required for get_order_book")
            return None
        endpoint = f"{self.BASE_URL}/orderbook"
        params = {"symbol": symbol}
        self.logger.info(f"Fetching orderbook for {symbol}")

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.exception(f"Failed to fetch orderbook for {symbol}: {e}")
            return None

    def get_ticker_list(self, contract_type=None):
        """Market data for ALL contracts + indices (broad monitoring)."""
        endpoint = f"{self.BASE_URL}/tickers"
        if contract_type: 
            params = {"contractType": contract_type}
            self.logger.info(f"Fetching market data for contract type {contract_type}")
        else:
            params = None
            self.logger.info(f"Fetching market data for all contract types")

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.exception("Failed to fetch market data")
            return None

# ----------------------------------------
    def get_ticker(self, symbol):
        """Market data for a single contract/index (lighter request)."""
        if symbol:
            endpoint = f"{self.BASE_URL}/tickers/{symbol}"
            self.logger.info(f"Fetching market data for symbol {symbol}")
        else:
            self.logger.error("symbol parameter is required for get_ticker")

        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            res = response.json()
            self.logger.info(f"Ticker with timestamp: {res['ticker'].get("lastTime")}")
            return res
            return response.json()
        except Exception as e:
            self.logger.exception("Failed to fetch market data")
            return None


    def get_instruments(self, contract_type=None):
        """Static metadata about all contracts (tick size, expiry, leverage)."""
        endpoint = f"{self.BASE_URL}/instruments"

        params = None
        if contract_type:
            if isinstance(contract_type, str):
                params = {"contractType": contract_type}
                self.logger.info(f"Fetching instruments of type {contract_type}")
            elif isinstance(contract_type, (list, tuple)):
                params = [("contractType", ct) for ct in contract_type]
                self.logger.info(f"Fetching instruments for contract types {', '.join(contract_type)}")
            else:
                raise ValueError("contract_type must be str, list or tuple")
        else:
            self.logger.info("Fetching instruments for all contract types")

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.exception("Failed to fetch instruments")
            return None

    def get_instrument_status_list(self, contract_type = None):
        """Market health for all instruments (halts, dislocations, volatility flags)."""
        endpoint = f"{self.BASE_URL}/instruments/status"

        params = None
        if contract_type:
            if isinstance(contract_type, str):
                params = {"contractType": contract_type}
                self.logger.info(f"Fetching status of instruments of type {contract_type}")
            elif isinstance(contract_type, (list, tuple)):
                params = [("contractType", ct) for ct in contract_type]
                self.logger.info(f"Fetching status of instruments for contract types {', '.join(contract_type)}")
            else:
                raise ValueError("contract_type must be str, list or tuple")
        else:
            self.logger.info("Fetching status of instruments for all contract types")

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.exception("Failed to fetch instrument status")
            return None
        

    def get_instrument_status(self, symbol):
        """Market health for one instrument (lighter request)."""

        if symbol:
            endpoint = f"{self.BASE_URL}/instruments/{symbol}/status"
            self.logger.info(f"Fetching status of instrument with symbol {symbol}")
        else:
            self.logger.error("symbol parameter is required for get_ticker")

        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.exception(f"Failed to fetch instrument status: {e}")
            return None
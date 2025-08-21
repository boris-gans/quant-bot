import os

KRAKEN_API_KEY = os.getenv("KRAKEN_PUB")
KRAKEN_API_SECRET = os.getenv("KRAKEN_PRIV")

# Defaults
EXCHANGE = "kraken"
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"

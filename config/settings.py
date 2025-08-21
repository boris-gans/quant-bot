import os

SANDBOX = os.getenv("SANDBOX")

if SANDBOX == True:
    KRAKEN_SAND_PUB = os.getenv("KRAKEN_PUB")
    KRAKEN_SAND_PRIV = os.getenv("KRAKEN_PRIV")
else:
    KRAKEN_API_KEY = os.getenv("KRAKEN_PUB")
    KRAKEN_API_SECRET = os.getenv("KRAKEN_PRIV")

# Defaults
EXCHANGE = "kraken"
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"

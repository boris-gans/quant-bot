import os
from dotenv import load_dotenv
load_dotenv()

SANDBOX = os.getenv("SANDBOX")

if SANDBOX == "True":
    KRAKEN_API_KEY = os.getenv("KRAKEN_SAND_PUB")
    KRAKEN_API_SECRET = os.getenv("KRAKEN_SAND_PRIV")
else:
    KRAKEN_API_KEY = os.getenv("KRAKEN_PUB")
    KRAKEN_API_SECRET = os.getenv("KRAKEN_PRIV")

DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PW = os.getenv("DATABASE_PW")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_URL = f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PW}@localhost:5432/{DATABASE_NAME}"

# Defaults
EXCHANGE = "krakenfutures"
SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"

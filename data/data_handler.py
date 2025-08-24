from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Numeric, 
    TIMESTAMP, ForeignKey, JSON, UniqueConstraint, Enum, Boolean, Float
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
# import enum

# -------------------------------
#           Schema def
# -------------------------------

Base = declarative_base()


class Index(Base):
    __tablename__ = "indices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)
    name = Column(String)
    base = Column(String)
    quote = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    instruments = relationship("Instrument", back_populates="index")
    statuses = relationship("InstrumentStatus", back_populates="index")

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)
    type = Column(String)                 # e.g., futures_inverse
    underlying = Column(String)           # link to index symbol
    index_id = Column(Integer, ForeignKey("indices.id"), nullable=True)
    tradeable = Column(Boolean)
    tick_size = Column(Numeric)
    contract_size = Column(Numeric)
    impact_mid_size = Column(Numeric)
    max_position_size = Column(Numeric)
    opening_date = Column(TIMESTAMP, nullable=True)
    funding_rate_coefficient = Column(Numeric)
    max_relative_funding_rate = Column(Numeric)
    isin = Column(String)
    contract_value_trade_precision = Column(Numeric)
    post_only = Column(Boolean)
    fee_schedule_uid = Column(String)
    mtf = Column(Boolean)
    base = Column(String)
    quote = Column(String)
    pair = Column(String)
    category = Column(String)
    tags = Column(JSON)                     # list of tags
    tradfi = Column(Boolean)

    # store complex nested structures as JSON
    margin_levels = Column(JSON)            # marginLevels
    retail_margin_levels = Column(JSON)     # retailMarginLevels
    margin_schedules = Column(JSON)         # marginSchedules

    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    index = relationship("Index", back_populates="instrument")
    statuses = relationship("InstrumentStatus", back_populates="instrument")
    trades = relationship("TradeHistory", back_populates="instrument")
    order_books = relationship("OrderBook", back_populates="instrument")
    tickers = relationship("Ticker", back_populates="instrument")

class InstrumentStatus(Base):
    __tablename__ = "instrument_status"

    id = Column(Integer, primary_key=True, autoincrement=True)

    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=True)
    index_id = Column(Integer, ForeignKey("indices.id"), nullable=True)

    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    status_flags = Column(JSON)             # full Kraken response
    is_halted = Column(Boolean)             # optional

    # Relationships
    instrument = relationship("Instrument", back_populates="statuses")
    index = relationship("Index", back_populates="statuses")

class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False, index=True, default=datetime.utcnow)
    price = Column(Numeric, nullable=False)
    size = Column(Numeric, nullable=False)
    side = Column(String, nullable=False)   # buy/sell
    type = Column(String, nullable=True)    # fill, etc.

    instrument = relationship("Instrument", back_populates="trades")

class OrderBook(Base):
    __tablename__ = "order_books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False, index=True, default=datetime.utcnow)
    bids = Column(JSON, nullable=False)   # save list of [price, size]
    asks = Column(JSON, nullable=False)   # save list of [price, size]

    instrument = relationship("Instrument", back_populates="order_books")

class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False, index=True, default=datetime.utcnow)

    # price info
    last = Column(Float, nullable=True)
    last_time = Column(TIMESTAMP, nullable=True)
    mark_price = Column(Float, nullable=True)
    bid = Column(Float, nullable=True)
    bid_size = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    ask_size = Column(Float, nullable=True)
    open24h = Column(Float, nullable=True)
    high24h = Column(Float, nullable=True)
    low24h = Column(Float, nullable=True)
    last_size = Column(Float, nullable=True)
    index_price = Column(Float, nullable=True)
    
    # trading info
    vol24h = Column(Float, nullable=True)
    volume_quote = Column(Float, nullable=True)
    open_interest = Column(Float, nullable=True)
    funding_rate = Column(Float, nullable=True)
    funding_rate_prediction = Column(Float, nullable=True)
    change24h = Column(Float, nullable=True)
    
    # status flags
    suspended = Column(Boolean, nullable=True)
    post_only = Column(Boolean, nullable=True)
    tag = Column(String, nullable=True)
    pair = Column(String, nullable=True)

    instrument = relationship("Instrument", back_populates="tickers")



class DataHandler:
    def __init__(self, db_url, logger):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)  # Creates tables if not exist
        self.Session = sessionmaker(bind=self.engine)

        self.logger = logger
        self.logger.info(f"Initialized DataHandler to DB: {db_url}")


    def add_instrument(self, instrument_data: dict):
        """Insert or update an instrument"""
        with self.Session() as session:
            inst = session.query(Instrument).filter_by(symbol=instrument_data["symbol"]).first()
            if not inst:
                inst = Instrument(**instrument_data)
                session.add(inst)
            else:
                for k, v in instrument_data.items():
                    setattr(inst, k, v)
            session.commit()
            self.logger.info("Added instrument data")
            return inst

    def add_trade(self, trade_data: dict):
        """Insert a trade into trade_history"""
        with self.Session() as session:
            trade = TradeHistory(**trade_data)
            session.add(trade)
            try:
                session.commit()
                self.logger.info("Added trade data")

            except Exception:
                session.rollback()  # ignore duplicate constraint
            return trade

    def get_trades_df(self, symbol: str):
        """Load trades into a pandas DataFrame"""
        import pandas as pd
        with self.Session() as session:
            inst = session.query(Instrument).filter_by(symbol=symbol).first()
            if not inst:
                return pd.DataFrame()
            trades = session.query(TradeHistory).filter_by(instrument_id=inst.instrument_id).all()
            df = pd.DataFrame([{
                "timestamp": t.timestamp,
                "side": t.side,
                "price": float(t.price),
                "size": float(t.size)
            } for t in trades])
            self.logger.info("Loaded trade data")

            return df.sort_values("timestamp")

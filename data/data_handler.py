from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Numeric, 
    TIMESTAMP, ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# -------------------------------
#           Schema def
# -------------------------------

Base = declarative_base()

class Instrument(Base):
    __tablename__ = "instruments"

    instrument_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)
    name = Column(String)
    contract_size = Column(Numeric)
    tick_size = Column(Numeric)
    leverage_min = Column(Numeric)
    leverage_max = Column(Numeric)
    margin_initial = Column(Numeric)
    margin_maintenance = Column(Numeric)
    settlement_type = Column(String)
    expiry = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    trades = relationship("TradeHistory", back_populates="instrument")
    tickers = relationship("Ticker", back_populates="instrument")
    statuses = relationship("InstrumentStatus", back_populates="instrument")

class InstrumentStatus(Base):
    __tablename__ = "instrument_status"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"))
    timestamp = Column(TIMESTAMP, nullable=False)
    status_flags = Column(JSON)

    instrument = relationship("Instrument", back_populates="statuses")
    __table_args__ = (UniqueConstraint("instrument_id", "timestamp", name="unique_status"),)

class TradeHistory(Base):
    __tablename__ = "trade_history"

    trade_id = Column(BigInteger, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"))
    exchange_trade_id = Column(String)
    timestamp = Column(TIMESTAMP, nullable=False)
    side = Column(String)
    price = Column(Numeric, nullable=False)
    size = Column(Numeric, nullable=False)

    instrument = relationship("Instrument", back_populates="trades")
    __table_args__ = (UniqueConstraint("instrument_id", "exchange_trade_id", name="unique_trade"),)

class OrderBookSnapshot(Base):
    __tablename__ = "order_book_snapshots"

    snapshot_id = Column(BigInteger, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"))
    timestamp = Column(TIMESTAMP, nullable=False)
    bids = Column(JSON, nullable=False)
    asks = Column(JSON, nullable=False)

    __table_args__ = (UniqueConstraint("instrument_id", "timestamp", name="unique_snapshot"),)

class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"))
    timestamp = Column(TIMESTAMP, nullable=False)
    last_price = Column(Numeric)
    mark_price = Column(Numeric)
    bid_price = Column(Numeric)
    ask_price = Column(Numeric)
    volume_24h = Column(Numeric)
    funding_rate = Column(Numeric)
    open_interest = Column(Numeric)

    instrument = relationship("Instrument", back_populates="tickers")
    __table_args__ = (UniqueConstraint("instrument_id", "timestamp", name="unique_ticker"),)




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

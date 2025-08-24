from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Numeric, 
    TIMESTAMP, ForeignKey, JSON, UniqueConstraint, Enum, Boolean, Float
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
# import enum

# -------------------------------
#           Schema def
# -------------------------------

Base = declarative_base()


class Indices(Base):
    __tablename__ = "indices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)
    name = Column(String)
    base = Column(String)
    quote = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    instrument = relationship("Instrument", back_populates="index")
    # statuses = relationship("InstrumentStatus", back_populates="indices")

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)
    type = Column(String)                        # e.g., futures_inverse
    underlying = Column(String)                  # link to index symbol
    index_id = Column(Integer, ForeignKey("indices.id", ondelete="CASCADE"), nullable=True)
    tradeable = Column(Boolean)
    tickSize = Column(Numeric)
    contractSize = Column(Numeric)
    impactMidSize = Column(Numeric)
    maxPositionSize = Column(Numeric)
    openingDate = Column(TIMESTAMP, nullable=True)
    fundingRateCoefficient = Column(Numeric)
    maxRelativeFundingRate = Column(Numeric)
    isin = Column(String)
    lastTradingTime = Column(TIMESTAMP, nullable=True)
    contractValueTradePrecision = Column(Numeric)
    postOnly = Column(Boolean)
    feeScheduleUid = Column(String)
    mtf = Column(Boolean)
    base = Column(String)
    quote = Column(String)
    pair = Column(String)
    category = Column(String)
    tags = Column(JSON)                          # list of tags
    tradfi = Column(Boolean)

    # store complex nested structures as JSON
    marginLevels = Column(JSON)                  # marginLevels
    retailMarginLevels = Column(JSON)           # retailMarginLevels
    marginSchedules = Column(JSON)              # marginSchedules

    created_at = Column(TIMESTAMP, default=datetime.utcnow)


    # Relationships
    index = relationship("Indices", back_populates="instrument")
    statuses = relationship("InstrumentStatus", back_populates="instrument")
    trades = relationship("TradeHistory", back_populates="instrument")
    order_books = relationship("OrderBook", back_populates="instrument")
    tickers = relationship("Ticker", back_populates="instrument")

class InstrumentStatus(Base):
    __tablename__ = "instrument_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=True)

    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    experiencingDislocation = Column(Boolean)
    priceDislocationDirection = Column(String)
    experiencingExtremeVolatility = Column(Boolean)
    extremeVolatilityInitialMarginMultiplier = Column(Integer)

    is_halted = Column(Boolean, nullable=True)             # optional

    # Relationships
    instrument = relationship("Instrument", back_populates="statuses")

class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False, index=True, default=datetime.utcnow)
    price = Column(Numeric, nullable=False)
    size = Column(Numeric, nullable=False)
    side = Column(String, nullable=False)   # buy/sell
    type = Column(String, nullable=True)    # fill, etc.

    instrument = relationship("Instrument", back_populates="trades")

class OrderBook(Base):
    __tablename__ = "order_books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False, index=True, default=datetime.utcnow)
    bids = Column(JSON, nullable=False)   # save list of [price, size]
    asks = Column(JSON, nullable=False)   # save list of [price, size]

    instrument = relationship("Instrument", back_populates="order_books")

class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
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


    def init_instruments(self, instrument_list: list):
        """
        Overwrite instruments table with new data.
        Non-tradeable instruments are also added to the indices table.
        """
        try:
            with self.Session() as session:
                # Delete all existing instruments and indices
                session.query(Instrument).delete()
                session.query(Indices).delete()
                session.commit()
                self.logger.info("Cleared existing instruments and indices")

                for instrument_data in instrument_list:
                    # Add to instruments table
                    inst = Instrument(**instrument_data)
                    session.add(inst)

                    # If not tradeable, also add to indices
                    if not instrument_data.get("tradeable", True):
                        index_data = {
                            "symbol": instrument_data["symbol"],
                            "name": instrument_data.get("name"),
                            # add other fields as needed
                        }
                        session.add(Indices(**index_data))

                session.commit()
                self.logger.info(f"Inserted {len(instrument_list)} instruments successfully")
                return "success"

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Failed to add instruments: {e}")
            return "fail"
        
    def save_instrument_status(self, status_data: dict):
        # Upsert either a list or a single instrument's status

        with self.Session() as session:
            try:
                statuses_to_add = []

                if "instrumentStatus" in status_data:
                    raw_statuses = status_data["instrumentStatus"]
                else:
                    raw_statuses = [status_data]

                # Collect all instrument IDs and generate map
                instrument_symbols = [s.get("tradeable") for s in raw_statuses if s.get("tradeable")]
                instruments = session.query(Instrument).filter(Instrument.symbol.in_(instrument_symbols)).all()
                instrument_map = {inst.symbol: inst.id for inst in instruments}

                if not instrument_map:
                    self.logger.warning("No matching instruments found for provided statuses")
                    return False

                # Delete old statuses for provided instruments
                session.query(InstrumentStatus).filter(InstrumentStatus.instrument_id.in_(instrument_map.values())).delete(synchronize_session=False)

                # Add new statuses
                for s in raw_statuses:
                    # print(s)
                    tradeable_symbol = s.get("tradeable")
                    instrument_id = instrument_map.get(tradeable_symbol)
                    if not instrument_id:
                        self.logger.warning(f"Skipping status, no instrument found for symbol {tradeable_symbol}")
                        continue

                    status_record = InstrumentStatus(
                        instrument_id=instrument_id,
                        experiencingDislocation=s['experiencingDislocation'],
                        priceDislocationDirection=s['priceDislocationDirection'],
                        experiencingExtremeVolatility=s['experiencingExtremeVolatility'],
                        extremeVolatilityInitialMarginMultiplier=s['extremeVolatilityInitialMarginMultiplier']
                        # optional isHalted field
                    )
                    statuses_to_add.append(status_record)

                if statuses_to_add:
                    session.add_all(statuses_to_add)
                    session.commit()
                    self.logger.info(f"Overwritten {len(statuses_to_add)} instrument status records")
                else:
                    self.logger.info("No valid instrument statuses to save")

            except SQLAlchemyError as e:
                session.rollback()
                self.logger.error(f"Failed to save instrument statuses: {str(e)}")
                return False

        return True

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

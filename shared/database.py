import os
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

# Using 'flex_' prefix to ensure clean separation from other projects in the same DB

class FlexGuildConfig(Base):
    __tablename__ = 'flex_guild_config'

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, unique=True, nullable=False)
    collection_slug = Column(String, nullable=False)

class FlexPlayer(Base):
    __tablename__ = 'flex_players'

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger, unique=True, nullable=False)
    wallet_address = Column(String, nullable=True)

class FlexNFT(Base):
    __tablename__ = 'flex_nfts'

    mint = Column(String, primary_key=True)
    collection_slug = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    rank = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)
    attributes = Column(JSON, nullable=True) # Stores list of {name, value, rarity}
    owner_wallet = Column(String, nullable=True, index=True)
    last_updated = Column(Float, nullable=True) # Timestamp

    
def get_engine():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in .env")
    return create_engine(DATABASE_URL)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)

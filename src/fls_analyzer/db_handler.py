# src/fls_analyzer/db_handler.py

import os
from sqlalchemy import (create_engine, Column, Integer, String, Text, 
                        ForeignKey, DateTime, Boolean, JSON)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

# Define the base class for declarative models
Base = declarative_base()

# Database path configuration
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
DB_PATH = os.path.join(DB_DIR, 'fls_data.db')


# --- ORM Models ---

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False) # "UCL 2025" or "NHL Stanley Cup 2025"
    
    # Relationships
    aggregators = relationship("Aggregator", back_populates="event")
    urls = relationship("ScrapedURL", back_populates="event")


class Aggregator(Base):
    __tablename__ = 'aggregators'
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'))
    
    # Relationships
    event = relationship("Event", back_populates="aggregators")
    scraped_urls = relationship("ScrapedURL", back_populates="source_aggregator")


class ScrapedURL(Base):
    __tablename__ = 'scraped_urls'
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    event_id = Column(Integer, ForeignKey('events.id'))
    aggregator_id = Column(Integer, ForeignKey('aggregators.id'))
    first_seen = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="urls")
    source_aggregator = relationship("Aggregator", back_populates="scraped_urls")
    security_analysis = relationship("SecurityAnalysis", back_populates="scraped_url", uselist=False, cascade="all, delete-orphan")
    privacy_analysis = relationship("PrivacyAnalysis", back_populates="scraped_url", uselist=False, cascade="all, delete-orphan")


class SecurityAnalysis(Base):
    __tablename__ = 'security_analysis'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('scraped_urls.id'), unique=True, nullable=False)
    
    vt_score = Column(Integer, default=0)
    is_phishing = Column(Boolean, default=False)
    drive_by_download_detected = Column(Boolean, default=False)
    # TODO: Maybe store full JSON report from Cuckoo? For now, just a path.
    malware_analysis_report = Column(Text)
    
    scraped_url = relationship("ScrapedURL", back_populates="security_analysis")


class PrivacyAnalysis(Base):
    __tablename__ = 'privacy_analysis'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('scraped_urls.id'), unique=True, nullable=False)

    # Storing the results from different vantage points as a JSON object.
    vp_analysis_data = Column(JSON)
    google_publisher_ids = Column(JSON)
    
    scraped_url = relationship("ScrapedURL", back_populates="privacy_analysis")


# --- Database Session Management ---

def get_engine():
    """Initializes the database engine."""
    os.makedirs(DB_DIR, exist_ok=True)
    return create_engine(f'sqlite:///{DB_PATH}')

def get_session():
    """Provides a database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Creates database tables from the models."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print(f"Database initialized at {DB_PATH}")
    
    # Pre-populate the events table
    session = get_session()
    if not session.query(Event).filter_by(name="UCL 2025").first():
        session.add(Event(name="UCL 2025"))
    if not session.query(Event).filter_by(name="NHL Stanley Cup 2025").first():
        session.add(Event(name="NHL Stanley Cup 2025"))
    session.commit()
    session.close()


# This allows the script to be run directly to set up the DB
if __name__ == '__main__':
    init_db()

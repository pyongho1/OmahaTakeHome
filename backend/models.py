from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    country = Column(String(64))
    latitude = Column(Float)
    longitude = Column(Float)
    region = Column(String(128))

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    display_name = Column(String(128))
    unit = Column(String(32))
    description = Column(String(512))

class ClimateData(Base):
    __tablename__ = "climate_data"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"), index=True, nullable=False)
    metric_id = Column(Integer, ForeignKey("metrics.id"), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    value = Column(Float, nullable=False)
    quality = Column(String(32), nullable=False)
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from .database import Base

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    light_level = Column(Float)

# Indexing timestamp for TimescaleDB optimization -> now just normal index
Index('idx_sensor_data_timestamp', SensorData.timestamp)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now())
    forecast_day = Column(Integer)  # 1 to 7
    predicted_temperature = Column(Float)
    predicted_humidity = Column(Float)
    predicted_pressure = Column(Float)
    rain_probability = Column(Float)


class AlertSubscriber(Base):
    __tablename__ = "alert_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now())
    alert_type = Column(String)  # 'rain', 'heat', 'humidity', 'pressure'
    message = Column(String)
    sent_to = Column(String)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="USER")  # "USER", "PENDING_ADMIN", "ADMIN"

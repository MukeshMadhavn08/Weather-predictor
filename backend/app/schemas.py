from pydantic import BaseModel, EmailStr
from typing import List

class SensorDataCreate(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    pressure: float
    light_level: float

class RealtimePredictionResponse(BaseModel):
    rain_probability: float
    predicted_temperature: float
    predicted_humidity: float
    predicted_pressure: float

class DailyForecast(BaseModel):
    day: int
    rain_probability: float
    temperature: float
    humidity: float
    pressure: float

class ForecastResponse(BaseModel):
    forecast: List[DailyForecast]

class EmailSubscribeRequest(BaseModel):
    email: EmailStr

from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "USER"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

import joblib
import os
import pandas as pd
import numpy as np
from datetime import datetime

MODEL_DIR = os.path.dirname(os.path.abspath(__file__)) + "/models"
rain_model = None
weather_reg_model = None

def load_models():
    global rain_model, weather_reg_model
    if rain_model is None or weather_reg_model is None:
        try:
            rain_model = joblib.load(os.path.join(MODEL_DIR, 'rain_model.joblib'))
            weather_reg_model = joblib.load(os.path.join(MODEL_DIR, 'weather_reg_model.joblib'))
        except FileNotFoundError:
            # If models not found, train them inline or raise error
            print("Models not found. Training needed.")
            # For simplicity in testing: return None
            return False
    return True

def predict_realtime(temperature: float, humidity: float, pressure: float, light_level: float, previous_rain: int = 0):
    if not load_models():
        return {"error": "Models not trained"}
        
    now = datetime.now()
    features = pd.DataFrame([{
        'temperature': temperature,
        'humidity': humidity,
        'pressure': pressure,
        'light_level': light_level,
        'hour_of_day': now.hour,
        'day_of_year': now.timetuple().tm_yday,
        'previous_rain': previous_rain
    }])
    
    # Get rain probability (class 1 probability)
    rain_prob = float(rain_model.predict_proba(features)[0][1]) * 100.0
    
    # Predict next reading (short-term forecast)
    next_weather = weather_reg_model.predict(features)[0]
    
    return {
        "rain_probability": round(rain_prob, 2),
        "predicted_temperature": round(float(next_weather[0]), 2),
        "predicted_humidity": round(float(next_weather[1]), 2),
        "predicted_pressure": round(float(next_weather[2]), 2)
    }

def predict_7_days(current_temp: float, current_hum: float, current_pres: float, current_light: float):
    if not load_models():
        return {"error": "Models not trained"}
        
    forecast = []
    
    now = datetime.now()
    feat_temp = current_temp
    feat_hum = current_hum
    feat_pres = current_pres
    feat_light = current_light
    prev_rain = 0
    
    for day_offset in range(1, 8):
        future_date = now + pd.Timedelta(days=day_offset)
        features = pd.DataFrame([{
            'temperature': feat_temp,
            'humidity': feat_hum,
            'pressure': feat_pres,
            'light_level': feat_light, # assuming light level might be similar or diurnal average
            'hour_of_day': 12, # predict for noon
            'day_of_year': future_date.timetuple().tm_yday,
            'previous_rain': prev_rain
        }])
        
        rain_prob = float(rain_model.predict_proba(features)[0][1]) * 100.0
        next_weather = weather_reg_model.predict(features)[0]
        
        forecast.append({
            "day": day_offset,
            "rain_probability": round(rain_prob, 2),
            "temperature": round(float(next_weather[0]), 2),
            "humidity": round(float(next_weather[1]), 2),
            "pressure": round(float(next_weather[2]), 2)
        })
        
        # update features for autoregressive forecasting
        feat_temp = float(next_weather[0])
        feat_hum = float(next_weather[1])
        feat_pres = float(next_weather[2])
        prev_rain = 1 if rain_prob > 50 else 0
        
    return {"forecast": forecast}

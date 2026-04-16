import pandas as pd
import numpy as np
import joblib
import os
import json
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, mean_absolute_error

MODEL_DIR = os.path.dirname(os.path.abspath(__file__)) + "/models"

def preprocess_data(df: pd.DataFrame):
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', dayfirst=True)
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_year'] = df['timestamp'].dt.dayofyear
    df = df.sort_values('timestamp')
    df['previous_rain'] = df['rain_observed'].shift(1).fillna(0)
    df = df.dropna()
    return df

def train_models(data_path: str) -> dict:
    print(f"Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print("Data file not found. Generating dummy data...")
        from .generate_dummy_data import generate_csv
        generate_csv(data_path)
        df = pd.read_csv(data_path)

    df = preprocess_data(df)

    features = ['temperature', 'humidity', 'pressure', 'light_level', 'hour_of_day', 'day_of_year', 'previous_rain']
    X = df[features]
    y_rain = df['rain_observed']

    df['next_temp'] = df['temperature'].shift(-1)
    df['next_hum'] = df['humidity'].shift(-1)
    df['next_pres'] = df['pressure'].shift(-1)
    df = df.dropna()
    X_reg = df[features]
    y_reg = df[['next_temp', 'next_hum', 'next_pres']]

    X_classifier = X.loc[X_reg.index]
    y_classifier = y_rain.loc[X_reg.index]

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_classifier, y_classifier, test_size=0.2, random_state=42)
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)

    print("Training Rain Classifier (XGBoost)...")
    rain_model = XGBClassifier(eval_metric='logloss')
    rain_model.fit(X_train_r, y_train_r)
    rain_preds = rain_model.predict(X_test_r)
    rain_accuracy = float(accuracy_score(y_test_r, rain_preds))
    print(f"Rain Classifier Accuracy: {rain_accuracy:.4f}")

    print("Training Weather Regressor (RandomForest MultiOutput)...")
    reg_model = MultiOutputRegressor(RandomForestRegressor(n_estimators=50, random_state=42))
    reg_model.fit(X_train_reg, y_train_reg)
    reg_preds = reg_model.predict(X_test_reg)
    mae = float(mean_absolute_error(y_test_reg, reg_preds))
    print(f"Weather Regressor MAE: {mae:.4f}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(rain_model, os.path.join(MODEL_DIR, 'rain_model.joblib'))
    joblib.dump(reg_model, os.path.join(MODEL_DIR, 'weather_reg_model.joblib'))
    print(f"Models saved to {MODEL_DIR}")

    metrics = {
        "rain_classifier_accuracy": round(rain_accuracy * 100, 2),
        "weather_regressor_mae": round(mae, 4),
        "training_samples": int(len(X_reg)),
        "last_trained": pd.Timestamp.now().isoformat()
    }
    with open(os.path.join(MODEL_DIR, 'metrics.json'), 'w') as f:
        json.dump(metrics, f)

    return metrics

if __name__ == "__main__":
    train_models(os.path.dirname(os.path.abspath(__file__)) + "/historical_weather.csv")

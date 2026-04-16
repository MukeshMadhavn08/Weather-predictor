import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_csv(filepath: str, rows: int = 5000):
    np.random.seed(42)
    start_date = datetime(2023, 1, 1)
    
    dates = [start_date + timedelta(hours=i) for i in range(rows)]
    temperatures = np.random.normal(25, 5, rows)
    humidities = np.random.normal(60, 15, rows).clip(0, 100)
    pressures = np.random.normal(1013, 10, rows)
    light_levels = np.random.normal(500, 200, rows).clip(0, 5000)
    
    # 0 or 1, higher chance if high humidity and low pressure
    rain_probs = 1 / (1 + np.exp(-(-5 + 0.1 * humidities - 0.05 * (pressures - 1000))))
    rain_observed = (np.random.rand(rows) < rain_probs).astype(int)
    
    df = pd.DataFrame({
        "timestamp": dates,
        "location": "TestCity",
        "temperature": temperatures,
        "humidity": humidities,
        "pressure": pressures,
        "light_level": light_levels,
        "rain_observed": rain_observed
    })
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Generated {rows} rows of dummy data at {filepath}")

if __name__ == "__main__":
    generate_csv("backend/app/ml/historical_weather.csv")

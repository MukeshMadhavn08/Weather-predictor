import requests
import time
import random

API_URL = "http://localhost:8000/api/sensors"

def simulate_sensor():
    while True:
        payload = {
            "device_id": "esp32_sim_1",
            "temperature": round(random.uniform(20.0, 38.0), 1),
            "humidity": round(random.uniform(40.0, 95.0), 1),
            "pressure": round(random.uniform(970.0, 1030.0), 1),
            "light_level": round(random.uniform(100.0, 1000.0), 1)
        }
        
        try:
            response = requests.post(API_URL, json=payload)
            print(f"Sent: {payload} -> Response: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(3)

if __name__ == "__main__":
    print("Starting ESP32 simulation...")
    simulate_sensor()

# 🌩️ IoT Weather Predictor & Forecast System

A state-of-the-art IoT telemetry monitoring, alerting, and machine learning-powered forecasting system. This application collects environmental data (temperature, humidity, barometric pressure, and light levels) from IoT devices (like an ESP32 or the provided simulation script), stores it, predicts rainfall in real-time, projects a 7-day weather forecast, and automates email alerts when critical thresholds are breached.

---

## 🏗️ System Architecture

The project consists of three main components:
1. **FastAPI Backend**: Ingests sensor data, drives the ML pipeline, manages user authentication/roles, and handles background email alerts.
2. **Next.js Frontend**: A modern, responsive dashboard with interactive visual charts (Recharts) and geospatial mapping (Leaflet) tracking active IoT nodes.
3. **IoT Simulator / ESP32 Client**: Simulates real-time environmental changes and pushes telemetry to the backend ingestion stream.

```mermaid
graph TD
    classDef client fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef server fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef storage fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff;
    classDef ml fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff;

    ESP32["ESP32 / Mock ESP32 Simulator"]:::client -->|HTTP POST /api/sensors| FastAPI["FastAPI API Gateway"]:::server
    NextJS["Next.js Web Frontend"]:::client -->|REST API Calls| FastAPI
    
    FastAPI -->|Async Write / Read| DB[("Database: SQLite / TimescaleDB")]:::storage
    FastAPI -->|Load ML Models| ML["ML Engine: XGBoost & Random Forest"]:::ml
    FastAPI -->|Background Tasks| Alert["Alert & Email Service"]:::server
    
    Alert -->|SMTP Protocol| Email["Email Subscribers"]:::client
```

---

## ✨ Features

- **Real-time Telemetry Ingestion**: High-throughput endpoint `/api/sensors` to capture IoT sensor telemetry.
- **Predictive ML Pipelines**:
  - **Rainfall Classifier (XGBoost)**: Predicts immediate rain probability based on current sensor parameters.
  - **Weather Regressor (Random Forest)**: An autoregressive multi-output regression model projecting a 7-day forecast (temperature, humidity, barometric pressure).
- **Interactive Dashboards**:
  - **Real-time Analytics**: Displays live-updating temperature, humidity, pressure, light levels, and rain forecasts.
  - **Geospatial Tracking**: Map rendering with Leaflet showing the geographical coordinates of the active IoT node.
  - **Trend Analysis**: Recharts-based history charts visualizing the telemetry over time.
- **Automated Alerts**: Background workers dispatch warning emails to active subscribers using an SMTP server configuration when limits are breached:
  - 🌧️ **Rain Alert**: Rain probability > 70%
  - 🌡️ **Heat Alert**: Temperature > 35°C
  - 💧 **Humidity Alert**: Humidity > 90%
  - ⚠️ **Low Pressure Alert**: Pressure < 980 hPa
- **ML Management Tools**: Authenticated administrators can upload new datasets (.csv) and trigger model retraining directly from the UI.
- **Role-Based Access Control**:
  - **Admin**: Complete system overview, subscriber management, database upload, and ML retraining.
  - **User / Subscriber**: Personalized telemetry dashboard and subscription controls.

---

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Asynchronous Python web framework for building APIs.
- **SQLAlchemy (Async)**: Modern async SQL toolkit for object-relational mapping.
- **SQLite / TimescaleDB**: Fast relational storage for time-series telemetry data.
- **Scikit-Learn & XGBoost**: Machine learning libraries for classifier and regression models.
- **Uvicorn**: High-performance ASGI server implementation.

### Frontend
- **Next.js (v16)**: React application framework utilizing the App Router.
- **Tailwind CSS (v4)**: Modern CSS styling for responsive layouts.
- **Recharts**: Composited charting library for rendering time-series graphs.
- **React Leaflet**: Mobile-friendly interactive maps.

---

## 📁 Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── ml/
│   │   │   ├── models/                   # Serialized ML models (*.joblib) and metrics.json
│   │   │   ├── generate_dummy_data.py    # Seed generator for historical weather dataset
│   │   │   ├── predict.py                # Core model load and inference logic
│   │   │   └── train.py                  # Model training and optimization script
│   │   ├── routers/
│   │   │   ├── api.py                    # Sensor ingestion, forecast, and ML endpoints
│   │   │   └── auth.py                   # User authentication & JWT management
│   │   ├── services/
│   │   │   └── email.py                  # Threshold validation & SMTP alert dispatch
│   │   ├── database.py                   # Async connection pool manager
│   │   ├── models.py                     # SQLAlchemy database model models
│   │   ├── schemas.py                    # Pydantic data validation schemas
│   │   └── main.py                       # FastAPI server instance initialization
│   ├── .env                              # Backend configuration / environment secrets
│   ├── mock_esp32.py                     # Mock client to simulate ESP32 HTTP requests
│   └── requirements.txt                  # Python dependencies list
│
├── frontend/
│   ├── src/
│   │   ├── app/                          # Next.js App Router views (Dashboards, Auth, ML)
│   │   ├── components/                   # Reusable components (Metrics, Charts, Navigation)
│   │   └── lib/                          # Client-side API fetchers and helpers
│   ├── package.json                      # Node.js dependencies and scripts
│   └── tsconfig.json                     # TypeScript compiler settings
│
├── docker-compose.yml                    # Docker orchestration for TimescaleDB service
├── start.bat                             # Batch script to simultaneously start all servers
└── README.md                             # Project documentation (this file)
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: v3.10 or higher
- **Node.js**: v18.0 or higher
- **Docker** (Optional, required for TimescaleDB)

---

### 2. Environment Setup

Configure the environment variables in `backend/.env`. A template is provided below:

```ini
# Email settings for SMTP (Gmail SMTP example)
SMTP_EMAIL=mukeshmadhavan.edu@gmail.com
SMTP_PASSWORD=your_app_specific_password  # Do not use your primary password!

# Admin details
ADMIN_USERNAME=admin
ADMIN_PASSWORD=14082007

# Database Connection (SQLite default, or TimescaleDB)
DATABASE_URL=sqlite+aiosqlite:///./weather.db
```

> [!NOTE]
> To configure email alerts via Gmail, you must generate an **App Password** from your Google Account settings under the Security tab.

---

### 3. Quick Run (Windows)

Simply double-click the `start.bat` file in the project root. This command will:
1. Fire up the FastAPI backend on `http://localhost:8000`.
2. Start the Next.js development server on `http://localhost:3000`.

Open your browser and navigate to [http://localhost:3000](http://localhost:3000) to view the application.

---

### 4. Manual Setup

If you are running on a non-Windows OS, or wish to start services manually, follow these steps:

#### Step A: Run the Database (Optional)
If you want to use **TimescaleDB** instead of SQLite:
```bash
docker-compose up -d
```
Then, update `DATABASE_URL` in `backend/.env` to point to your Postgres instance (e.g. `postgresql+asyncpg://user:password@localhost:5432/weather_db`).

#### Step B: Launch Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Train the ML models (if not already trained):
   ```bash
   python -m app.ml.train
   ```
5. Run the development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Step C: Launch Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Launch development server:
   ```bash
   npm run dev
   ```

#### Step D: Run the ESP32 Simulation
To feed live sensor telemetry into the dashboard, start the mock simulator:
```bash
cd backend
python mock_esp32.py
```
This script will post simulated sensor readings to the API every 3 seconds.

---

## 🔐 Credentials & Default Accounts

To explore the dashboard:
- **Default Administrator**:
  - **Username**: `admin`
  - **Password**: `14082007` (configured in `.env`)

---

## 📡 API Reference & Integration

### IoT Sensor Ingestion
Any physical IoT node can publish telemetry. Point your device to:

* **Endpoint**: `POST /api/sensors`
* **Content-Type**: `application/json`
* **Request Payload**:
  ```json
  {
    "device_id": "esp32_station_01",
    "temperature": 27.5,
    "humidity": 65.0,
    "pressure": 1012.3,
    "light_level": 450.0
  }
  ```

### Real-Time Weather Prediction
Get instantaneous forecasting results on custom parameters.

* **Endpoint**: `POST /api/realtime-predict`
* **Request Payload**: (Same as above)
* **Response Payload**:
  ```json
  {
    "rain_probability": 15.42,
    "predicted_temperature": 28.1,
    "predicted_humidity": 63.8,
    "predicted_pressure": 1011.9
  }
  ```

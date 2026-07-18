from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import os
import json
import shutil

from ..schemas import SensorDataCreate, EmailSubscribeRequest, RealtimePredictionResponse, ForecastResponse
from ..database import get_db
from ..models import SensorData, AlertSubscriber, User
from ..ml.predict import predict_realtime, predict_7_days
from ..services.email import check_alerts_and_notify
from .auth import get_current_admin_user, get_current_active_user

router = APIRouter()

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml', 'models')
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml', 'historical_weather.csv')


# ─── Sensor Ingestion ───────────────────────────────────────────────────────

@router.post("/sensors")
async def ingest_sensor_data(data: SensorDataCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    new_data = SensorData(
        device_id=data.device_id,
        temperature=data.temperature,
        humidity=data.humidity,
        pressure=data.pressure,
        light_level=data.light_level
    )
    db.add(new_data)
    await db.commit()

    # Run ML prediction safely — never block the response
    try:
        prediction = predict_realtime(
            temperature=data.temperature,
            humidity=data.humidity,
            pressure=data.pressure,
            light_level=data.light_level
        )

        if "error" not in prediction:
            background_tasks.add_task(
                check_alerts_and_notify,
                db=db,
                rain_prob=prediction["rain_probability"],
                temp=data.temperature,
                humidity=data.humidity,
                pressure=data.pressure
            )
    except Exception as e:
        print(f"ML prediction error (non-fatal): {e}")

    return {"status": "stored", "device": data.device_id}

@router.get("/sensors/latest")
async def get_latest_sensor_data(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SensorData).order_by(SensorData.id.desc()).limit(1))
    latest = result.scalar_one_or_none()
    
    if not latest:
        # Fallback static data if the ESP32 hasn't sent anything yet and DB is empty
        return {
            "device_id": "fallback_static",
            "temperature": 25.0,
            "humidity": 60.0,
            "pressure": 1013.0,
            "light_level": 300.0,
            "timestamp": "2026-01-01T12:00:00",
            "rain_probability": 0.0
        }
    
    # Also get the prediction for this latest data
    prediction = predict_realtime(
        temperature=latest.temperature,
        humidity=latest.humidity,
        pressure=latest.pressure,
        light_level=latest.light_level
    )
    
    return {
        "device_id": latest.device_id,
        "temperature": latest.temperature,
        "humidity": latest.humidity,
        "pressure": latest.pressure,
        "light_level": latest.light_level,
        "timestamp": latest.timestamp.isoformat(),
        "rain_probability": prediction.get("rain_probability", 0)
    }



# ─── Predictions ─────────────────────────────────────────────────────────────

@router.post("/realtime-predict", response_model=RealtimePredictionResponse)
async def get_realtime_prediction(data: SensorDataCreate):
    prediction = predict_realtime(
        temperature=data.temperature,
        humidity=data.humidity,
        pressure=data.pressure,
        light_level=data.light_level
    )
    if "error" in prediction:
        raise HTTPException(status_code=500, detail=prediction["error"])
    return prediction


@router.get("/predict-7days", response_model=ForecastResponse)
async def get_7_day_forecast(
    temp: float = 25.0,
    hum: float = 60.0,
    pres: float = 1013.0,
    light: float = 500.0
):
    forecast = predict_7_days(
        current_temp=temp,
        current_hum=hum,
        current_pres=pres,
        current_light=light
    )
    if "error" in forecast:
        raise HTTPException(status_code=500, detail=forecast["error"])
    return forecast


# ─── Email Subscribers ────────────────────────────────────────────────────────

@router.post("/subscribe-email")
async def subscribe_email(req: EmailSubscribeRequest, db: AsyncSession = Depends(get_db)):
    new_sub = AlertSubscriber(email=req.email)
    db.add(new_sub)
    try:
        await db.commit()
        return {"status": "subscribed", "email": req.email}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already subscribed or invalid.")


@router.get("/subscribers")
async def list_subscribers(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(AlertSubscriber).where(AlertSubscriber.is_active == True))
    subscribers = result.scalars().all()
    return {"subscribers": [{"id": s.id, "email": s.email} for s in subscribers]}


@router.delete("/subscribers/{email}")
async def delete_subscriber(
    email: str, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    await db.execute(delete(AlertSubscriber).where(AlertSubscriber.email == email))
    await db.commit()
    return {"status": "deleted", "email": email}


# ─── ML Management ────────────────────────────────────────────────────────────

@router.get("/ml/history")
async def get_ml_history():
    """Return historical dataset as JSON for frontend graphs."""
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="No historical dataset available.")
    
    import pandas as pd
    try:
        df = pd.read_csv(DATA_PATH)
        # Parse timestamp to ensure proper sorting, keep last 100 rows for performance
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp']).sort_values('timestamp')
            
        # Select key columns and tail
        cols = [c for c in ['timestamp', 'temperature', 'humidity', 'pressure', 'light_level', 'rain_observed'] if c in df.columns]
        recent_history = df[cols].tail(100).copy()
        
        # Convert timestamps back to ISO strings for JSON serialization
        if 'timestamp' in recent_history.columns:
            recent_history['timestamp'] = recent_history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
        return recent_history.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dataset: {str(e)}")

@router.get("/ml/metrics")
async def get_ml_metrics():
    metrics_path = os.path.join(MODEL_DIR, 'metrics.json')
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="No metrics available. Please train the model first.")
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    return metrics


@router.post("/ml/retrain")
async def retrain_model(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin_user)
):
    """Upload a CSV dataset and retrain the ML models."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    # Save uploaded CSV
    with open(DATA_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run training synchronously (for simplicity; long-running in prod should be async)
    try:
        from ..ml.train import train_models
        metrics = train_models(DATA_PATH)
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


# Old Auth replaced by auth.py router

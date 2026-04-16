from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import contextlib
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from .database import engine, Base


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown logic if any

app = FastAPI(title="IoT Weather Forecast API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import api, auth

@app.get("/")
async def root():
    return {"message": "Welcome to the IoT Weather Forecast API"}

app.include_router(auth.router, prefix="/api")
app.include_router(api.router, prefix="/api")

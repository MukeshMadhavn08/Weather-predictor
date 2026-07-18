from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./weather.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Prevents QueuePool overflow with SQLite
    connect_args={"timeout": 30}  # Wait up to 30s for lock
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

# Enable WAL mode for better concurrent read/write performance
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


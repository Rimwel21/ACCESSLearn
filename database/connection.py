from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# SQLite requires check_same_thread=False for FastAPI's async threading
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine_kwargs = {"connect_args": connect_args}
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    })

engine = create_engine(settings.database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

Base = declarative_base()

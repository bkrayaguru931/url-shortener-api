import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL connection string, configurable via environment variable.
# Format: postgresql://<user>:<password>@<host>:<port>/<database>
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/url_shortener",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and
    guarantees it is closed after the request finishes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

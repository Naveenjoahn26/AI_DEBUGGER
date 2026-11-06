from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logger import logger


try:

    engine = create_engine(settings.DATABASE_URL)
    logger.info("Database engine created successfully")
except SQLAlchemyError as e:
    logger.error(f"Database connection failed: {e}")
    raise SystemExit(1)
    
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    pass
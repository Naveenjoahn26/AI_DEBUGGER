from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter,Depends
from app.core.logger import logger
from app.schemas.response import APIResponse
from app.db.session import  get_db,Base,engine,Session
from sqlalchemy import text
import sqlite3
router = APIRouter(prefix="/health",tags=["User Management"])




@router.get("/", response_model=APIResponse)
def get_health(db: Session = Depends(get_db)):

    logger.info("Health check requested.")

    try:
        db.execute(text("SELECT 1"))

        return APIResponse(
            success=True,
            message="System is healthy.",
            data={
                "database": "connected"
            }
        )

    except Exception as e:

        logger.exception(e)

        return APIResponse(
            success=False,
            message="System health check failed.",
            data={
                "database": "disconnected"
            }
        )
@router.get("/error")
async def test_error():
    raise Exception("Testing exception handler")

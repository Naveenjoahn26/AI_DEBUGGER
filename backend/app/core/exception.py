from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logger import logger

def register_exception_handlers(app:FastAPI):

    @app.exception_handler(Exception)
    async def global_exception_handler(request:Request,exc:Exception):
        print("✅ Global Exception Handler Executed")
        logger.exception(f"Unhandled exception occurs:{exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success":False,
                "error":{
                    "type":"InternalServerError",
                    "message":"Something went wrong."
                }
            }
        )

import logging
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

from assets import api
from endpoints import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autopaint-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AutoPaint API")
    api.avail = 'AVAILABLE'

    try:
        yield
    finally:
        api.avail = 'UNAVAILABLE'
        api.close()
        logger.info("API marked UNAVAILABLE")


app = FastAPI(
    title="AutoPaint API",
    version=os.environ.get('APPLICATION_VERSION'),
    lifespan=lifespan
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9080, reload=True)

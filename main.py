from fastapi import FastAPI
from app.logging import setup_logging
from app.api.api import api_router


app = FastAPI()

# initialize logging
setup_logging()


@app.route("/")
async def index():
    return "fastapi server running"


app.include_router(api_router)

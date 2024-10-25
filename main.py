from fastapi import FastAPI
from app.logging import setup_logging


app = FastAPI()

# initialize logging
setup_logging()


@app.route("/")
async def index():
    return "fastapi server running"

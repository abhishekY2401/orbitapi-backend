from fastapi import APIRouter
from app.api.endpoints import repository

api_router = APIRouter()
api_router.include_router(
    repository.router, prefix='/repo', tags=['repository'])

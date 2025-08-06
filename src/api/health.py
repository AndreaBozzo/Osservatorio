from fastapi import APIRouter
from datetime import datetime
import os

health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.get("/live")
async def liveness_check():
    """Basic liveness check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "osservatorio-api"
    }

@health_router.get("/ready") 
async def readiness_check():
    """Basic readiness check"""
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }

from datetime import datetime

import aiohttp
import asyncpg
from fastapi import APIRouter
from redis import asyncio as aioredis

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/live")
async def liveness_check():
    """Basic liveness check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "osservatorio-api",
    }


@health_router.get("/ready")
async def readiness_check():
    """Basic readiness check"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@health_router.get("/db")
async def db_health_check():
    try:
        # Establish a connection to the database
        conn = await asyncpg.connect(
            host="postgres",
            port=5432,
            user="osservatorio",
            password="osservatorio_dev_password",
            database="osservatorio"
        )

        # Execute a simple query to verify the database's status
        await conn.execute("SELECT 1")

        # Close the connection
        await conn.close()

        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except asyncpg.exceptions.DatabaseError as e:
        return {"status": "unhealthy", "error": str(e)}


@health_router.get("/cache")
async def cache_health_check():
    try:
        # Establish a connection to the Redis server
        redis = await aioredis.create_redis_pool("redis://redis:6379/0")

        # Execute a PING command to verify the Redis server's status
        await redis.ping()

        # Close the connection
        redis.close()
        await redis.wait_closed()

        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except aioredis.exceptions.RedisError as e:
        return {"status": "unhealthy", "error": str(e)}


@health_router.get("/external")
async def external_health_check():
    # try:
    #     # Send an HTTP request to the REST endpoint
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get("https://sdmx.istat.it/SDMXWS/rest") as response:
    #             # Verify that the response status code is 200 (OK)
    #             if response.status != 200:
    #                 return {"status": "unhealthy", "error": f"Invalid status code: {response.status}"}

    #             # Verify that the response body contains the expected data
    #             health_check_data = await response.json()
    #             if health_check_data.get("status") != "healthy":
    #                 return {"status": "unhealthy", "error": f"Invalid health check data: {health_check_data}"}

    #     return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    # except aiohttp.ClientError as e:
    #     return {"status": "unhealthy", "error": str(e)}
    # TODO: find a way to test helth of REST ISTAT service
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@health_router.get("/metrics")
async def metrics_health_check():
    try:
        # Send an HTTP request to the Prometheus server's /-/healthy endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get("http://prometheus:9090/-/healthy") as response:
                # Verify that the response status code is 200 (OK)
                if response.status != 200:
                    return {"status": "unhealthy", "error": f"Invalid status code: {response.status}"}

                # Verify that the response body contains the expected health check data
                health_check_data = await response.text()
                if health_check_data != "Healthy":
                    return {"status": "unhealthy", "error": f"Invalid health check data: {health_check_data}"}

        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except aiohttp.ClientError as e:
        return {"status": "unhealthy", "error": str(e)}

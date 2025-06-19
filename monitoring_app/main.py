from fastapi import FastAPI, Response
from metrics_collector import MetricsCollector, ServiceConfig
import asyncio
import os
import uvicorn

app = FastAPI(title="Prometheus Monitoring Service")

# Configure monitored services
services = [
    ServiceConfig(
        name="ml-app",
        url=os.getenv("ML_APP_URL", "http://ml-app-service:8000"),
        health_endpoint="/"
    ),
    ServiceConfig(
        name="dispatcher",
        url=os.getenv("DISPATCHER_URL", "http://dispatcher-service:8001"),
        health_endpoint="/"
    )
]

# Initialize metrics collector
metrics_collector = MetricsCollector(services)

@app.on_event("startup")
async def startup_event():
    """Start metrics collection on app startup"""
    await metrics_collector.start_collection(interval=10.0)

@app.on_event("shutdown")
async def shutdown_event():
    """Stop metrics collection on app shutdown"""
    await metrics_collector.stop_collection()

@app.get("/")
async def root():
    return {
        "message": "Prometheus Monitoring Service",
        "monitored_services": [s.name for s in services],
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    metrics = metrics_collector.get_prometheus_metrics()
    return Response(content=metrics, media_type="text/plain")

@app.get("/status")
async def get_status():
    """Get status of all monitored services"""
    return await metrics_collector.get_service_status()

@app.get("/services")
async def get_services():
    """Get list of monitored services"""
    return {
        "services": [
            {
                "name": s.name,
                "url": s.url,
                "health_endpoint": s.health_endpoint
            }
            for s in services
        ]
    }

if __name__ == "__main__":
    import time
    uvicorn.run(app, host="0.0.0.0", port=9000)
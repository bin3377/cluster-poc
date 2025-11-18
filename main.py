"""
FastAPI Cluster PoC Application
"""

import uvicorn
from fastapi import FastAPI

from app.routers import carpool

# Create FastAPI app
app = FastAPI(
    title="Cluster PoC API",
    description="FastAPI app of cluster-poc",
    version="1.0.0",
    debug=True,
)

# Include routers
app.include_router(carpool.router, prefix="/api/v1")


@app.get("/echo")
async def echo():
    """Health check endpoint"""
    from datetime import datetime

    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

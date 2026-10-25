import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database.db import init_db
from .services.model_service import model_service
from .services.resource_monitor import resource_monitor
from .schemas.schemas import HealthResponse, ModelInfoResponse
from .utils.logger import logger

from .api.routes_translation import router as translation_router
from .api.routes_benchmark import router as benchmark_router
from .api.routes_datasets import router as datasets_router
from .api.routes_experiments import router as experiments_router
from .api.routes_cost import router as cost_router

# Initialize database schema on startup
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Research API comparing Greedy and Beam Search decoding in Indic Machine Translation."
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(translation_router, prefix=settings.API_PREFIX)
app.include_router(benchmark_router, prefix=settings.API_PREFIX)
app.include_router(datasets_router, prefix=settings.API_PREFIX)
app.include_router(experiments_router, prefix=settings.API_PREFIX)
app.include_router(cost_router, prefix=settings.API_PREFIX)

@app.get(f"{settings.API_PREFIX}/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Returns system status, active model state, and RAM utilization."""
    sys_m = resource_monitor.get_system_metrics()
    return HealthResponse(
        status="healthy",
        model_loaded=model_service.is_loaded,
        model_name=model_service.model_name,
        device=model_service.device,
        system_ram_gb=sys_m["system_ram_gb"],
        ram_usage_percent=sys_m["ram_usage_percent"],
        cpu_percent=sys_m["cpu_percent"]
    )

@app.get(f"{settings.API_PREFIX}/model/info", response_model=ModelInfoResponse, tags=["Model"])
async def get_model_info():
    """Returns metadata about the configured neural machine translation checkpoint."""
    info = model_service.get_info()
    return ModelInfoResponse(**info)

@app.post(f"{settings.API_PREFIX}/model/load", tags=["Model"])
async def load_model():
    """Manually pre-warms and loads the neural machine translation model."""
    success = model_service.load_model()
    return {
        "message": "Model loaded successfully.",
        "model_name": model_service.model_name,
        "load_time_seconds": model_service.init_duration_sec,
        "process_memory_mb": resource_monitor.get_process_memory_mb()
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": f"{settings.API_PREFIX}/health"
    }

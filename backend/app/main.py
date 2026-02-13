from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import get_cors_allow_origins, validate_runtime_config
from app.core.errors import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.middleware import install_request_middleware
from app.db.models import init_db


def create_app() -> FastAPI:
    setup_logging()
    validate_runtime_config()
    init_db()
    app = FastAPI(
        title="CarePath AI",
        description="MVP for patient referral path recommendation",
        version="0.1.0",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_request_middleware(app)
    register_exception_handlers(app)
    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()

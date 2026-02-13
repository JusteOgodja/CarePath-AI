from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_cors_allow_origins
from app.db.models import init_db


def create_app() -> FastAPI:
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
    
    app.include_router(router)
    return app


app = create_app()

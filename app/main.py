import os
from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database.sql_adaptor import Base, engine
from app.pipeline.pipeline_endpoint import router as pipeline_router
from typing import Any

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    
    Steps:
      1. Initializes the FastAPI app.
      2. Configures CORSMiddleware to allow all origins, credentials, methods, and headers.
      3. Includes the application routers.
      4. Calls Base.metadata.create_all(engine) to create all database tables.
    
    Returns:
        A configured FastAPI application instance.
    """
    app: FastAPI = FastAPI()

    # Configure CORS middleware with all origins allowed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Include the pipeline router
    app.include_router(pipeline_router)

    # Create all tables defined in the SQLAlchemy models
    Base.metadata.create_all(bind=engine)

    return app

# Create the FastAPI application instance to be imported elsewhere
app: FastAPI = create_app()

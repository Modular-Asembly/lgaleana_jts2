from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.database.sql_adaptor import Base, engine
from app.pipeline.pipeline_endpoint import router as pipeline_router

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    1. Calls load_dotenv() to load environment variables.
    2. Initializes the FastAPI app.
    3. Adds CORSMiddleware with permissive settings.
    4. Includes all application routers.
    5. Calls Base.metadata.create_all(engine) to create database tables.
    
    Returns:
        A configured FastAPI application instance.
    """
    # Load environment variables from .env file.
    load_dotenv()

    # Initialize FastAPI app.
    app = FastAPI()

    # Configure CORS middleware to allow all origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Include application routers.
    app.include_router(pipeline_router)

    # Create database tables using SQLAlchemy metadata.
    Base.metadata.create_all(bind=engine)

    return app

app = create_app()

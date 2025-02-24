import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Iterator

# Retrieve the database URL from environment variables.
DB_URL: str = os.getenv("DB_URL", "")
if not DB_URL:
    raise EnvironmentError("DB_URL environment variable is not set.")

# Initialize the SQLAlchemy engine using the provided DB_URL.
engine = create_engine(DB_URL, echo=False)

# Create a configured "SessionLocal" class.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Create a Base class for declarative class definitions.
Base = declarative_base()

def get_session() -> Iterator[Session]:
    """
    Creates a new SQLAlchemy Session, yields it for use in database interactions,
    and ensures it is closed after its usage.
    """
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create engine
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
else:
    engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()


def init_db():
    """Create all tables. For production, use Alembic migrations."""
    try:
        from app.models import db_models  # noqa: F401
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        pass


def get_db():
    """Yields a database session and closes it after the request."""
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

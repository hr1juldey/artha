"""Database connection management"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import DB_PATH

# Create base for models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH}",
    echo=False,  # Set True for debugging
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    """Initialize database and create tables"""
    from src.database.models import User, Game, Position  # Import here to avoid circular imports

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session
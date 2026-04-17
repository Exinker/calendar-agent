from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from database.config import DatabaseSettings

settings = DatabaseSettings()

Base = declarative_base()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=20,
    max_overflow=0,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
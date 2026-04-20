"""Pytest fixtures for integration tests with testcontainers."""
import pytest
import pytest_asyncio


# Check if Docker is available
def _is_docker_available():
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


DOCKER_AVAILABLE = _is_docker_available()


@pytest.fixture(scope="session")
def postgres_container():
    """Create PostgreSQL container for tests."""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker not available", allow_module_level=True)
    
    from testcontainers.postgres import PostgresContainer
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest_asyncio.fixture
async def db_engine(postgres_container):
    """Create async database engine connected to test container."""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker not available")
    
    from sqlalchemy.ext.asyncio import create_async_engine
    
    # Convert postgres URL to async format
    db_url = postgres_container.get_connection_url()
    # Replace postgresql:// with postgresql+psycopg://
    async_db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
    
    engine = create_async_engine(
        async_db_url,
        echo=False,
        pool_size=5,
        max_overflow=0,
    )
    
    from src.models.database_models import Base
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create database session for tests."""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker not available")
    
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        # Rollback after each test
        await session.rollback()


@pytest.fixture
def test_encryption_key():
    """Generate test encryption key."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()
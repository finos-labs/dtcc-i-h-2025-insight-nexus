from sqlalchemy import create_engine
from config import ENGINE_URL

# Create SQLAlchemy engine
engine = create_engine(
    ENGINE_URL,
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  
    pool_timeout=30,  # Wait time for a connection
    pool_recycle=3600  # Recycle connections after 1 hour to avoid stale states
)


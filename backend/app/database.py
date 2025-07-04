import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Database configuration
def get_database_url():
    """Get database URL based on environment"""
    
    # Check for custom DATABASE_URL (for production/testing)
    if database_url := os.getenv("DATABASE_URL"):
        return database_url
    
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # Running in Lambda - use SQLite for now (until we set up RDS)
        return "sqlite:////tmp/federal_budget.db"
    else:
        # Local development - use local PostgreSQL
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "federal_budget")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create database engine
database_url = get_database_url()

# Log database connection (hide password)
display_url = database_url
if "postgresql" in database_url and "@" in database_url:
    # Replace password with *** for display
    parts = database_url.split("://")[1].split("@")
    if ":" in parts[0]:
        user_pass = parts[0].split(":")
        display_url = f"postgresql://{user_pass[0]}:***@{parts[1]}"

print(f"🔗 Connecting to database: {display_url}")

if "postgresql" in database_url:
    # PostgreSQL-specific configuration
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
    )
else:
    # SQLite configuration (for Lambda)
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check function
def check_database_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False 
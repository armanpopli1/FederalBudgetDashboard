import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import boto3
import json

# Database configuration
# For local development, use DATABASE_URL environment variable
# For AWS Lambda, get credentials from Secrets Manager

def get_database_url():
    """Get database URL from environment or AWS Secrets Manager"""
    
    # Try environment variable first (for local development)
    if database_url := os.getenv("DATABASE_URL"):
        return database_url
    
    # For AWS Lambda, get from Secrets Manager
    try:
        secret_name = os.getenv("DB_SECRET_NAME", "federal-budget-db-credentials")
        region_name = os.getenv("AWS_REGION", "us-east-1")
        
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        secret_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(secret_response['SecretString'])
        
        return f"postgresql://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/{secret['dbname']}"
    
    except Exception as e:
        print(f"Error getting database credentials: {e}")
        raise

# Create database engine
database_url = get_database_url()
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=300,
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
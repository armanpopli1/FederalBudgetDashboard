#!/usr/bin/env python3
"""
Environment Setup Script for Federal Budget Dashboard Backend

This script helps set up the local development environment:
- Creates .env file with database configuration
- Tests database connection
- Creates database if it doesn't exist
- Runs initial migrations
"""

import os
import sys
import subprocess
from pathlib import Path

def create_env_file():
    """Create .env file with default configuration"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("📄 .env file already exists")
        return
    
    print("📄 Creating .env file...")
    
    # Get database password from user
    db_password = input("Enter PostgreSQL password (or press Enter for no password): ").strip()
    
    env_content = f"""# Federal Budget Dashboard - Development Environment
# Database Configuration
DB_USER=postgres
DB_PASSWORD={db_password}
DB_HOST=localhost
DB_PORT=5432
DB_NAME=federal_budget

# Debug Settings
DATABASE_DEBUG=false

# Development Settings
ENVIRONMENT=development
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file")

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

def test_postgres_connection():
    """Test if PostgreSQL is running and accessible"""
    print("🔍 Testing PostgreSQL connection...")
    
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    
    try:
        import psycopg2
        
        # Test connection to PostgreSQL server (without specific database)
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database="postgres"  # Default database
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running: brew services start postgresql")
        print("2. Check if database exists: psql -l")
        print("3. Check connection settings in .env file")
        return False

def create_database():
    """Create the federal_budget database if it doesn't exist"""
    print("🗄️  Creating database...")
    
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "federal_budget")
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Check if database exists
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Created database: {db_name}")
        else:
            print(f"✅ Database already exists: {db_name}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {str(e)}")
        return False

def test_application_db_connection():
    """Test database connection using application configuration"""
    print("🔗 Testing application database connection...")
    
    try:
        # Import after environment is set up
        from app.database import check_database_connection
        
        if check_database_connection():
            print("✅ Application database connection successful")
            return True
        else:
            print("❌ Application database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Application database connection error: {str(e)}")
        return False

def run_migrations():
    """Run database migrations to create tables"""
    print("🏗️  Running database migrations...")
    
    try:
        # Create all tables
        from app.database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🏛️  Federal Budget Dashboard - Environment Setup")
    print("=" * 50)
    
    # Step 1: Create .env file
    create_env_file()
    
    # Step 2: Load environment variables
    load_env_file()
    
    # Step 3: Test PostgreSQL connection
    if not test_postgres_connection():
        print("\n❌ Setup failed: PostgreSQL connection issues")
        print("\nNext steps:")
        print("1. Install PostgreSQL: brew install postgresql")
        print("2. Start PostgreSQL: brew services start postgresql")
        print("3. Set up database user if needed")
        print("4. Run this script again")
        return False
    
    # Step 4: Create database
    if not create_database():
        print("\n❌ Setup failed: Database creation issues")
        return False
    
    # Step 5: Test application database connection
    if not test_application_db_connection():
        print("\n❌ Setup failed: Application database connection issues")
        return False
    
    # Step 6: Run migrations
    if not run_migrations():
        print("\n❌ Setup failed: Database migration issues")
        return False
    
    print("\n🎉 Environment setup completed successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the application: python run_local.py")
    print("3. Import OBJCLASS data: python scripts/objclass_parser.py data/BUDGET-2026-OBJCLASS-1/Data-Table.csv")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
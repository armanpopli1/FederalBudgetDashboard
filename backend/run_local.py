"""
Local development server for Federal Budget Dashboard API

This script runs the FastAPI app locally using uvicorn for development and testing.
"""

import uvicorn
import os
from dotenv import load_dotenv

def main():
    """Run the local development server"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    print("🚀 Starting Federal Budget Dashboard API (Local Development)")
    print("=" * 60)
    
    # Check required environment variables
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("Please set your database connection string:")
        print("export DATABASE_URL='postgresql://user:password@host:5432/dbname'")
        print()
        print("Or create a .env file with your configuration")
        return
    
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'Not configured'}")
    print(f"CORS Origins: {os.getenv('CORS_ORIGINS', 'Default (localhost:3000)')}")
    print()
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 
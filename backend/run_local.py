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
    
    # Import and test database connection
    try:
        from app.database import check_database_connection
        if check_database_connection():
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            print("Please check your .env file configuration")
            return
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        print("Please check your .env file configuration")
        return
    
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
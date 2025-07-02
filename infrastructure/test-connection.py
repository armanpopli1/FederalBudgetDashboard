#!/usr/bin/env python3
"""
Test database connection script for Federal Budget Dashboard

This script tests the connection to the PostgreSQL RDS instance
and verifies basic functionality.
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def test_connection():
    """Test database connection and basic operations"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("Example: export DATABASE_URL='postgresql://user:password@host:5432/dbname'")
        return False
    
    try:
        # Parse the database URL
        parsed = urlparse(database_url)
        
        print("🔍 Testing database connection...")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path[1:]}")  # Remove leading slash
        print(f"   User: {parsed.username}")
        print()
        
        # Test connection
        print("1️⃣  Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        print("   ✅ Connection successful!")
        
        # Test basic query
        print("2️⃣  Testing basic query...")
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✅ PostgreSQL version: {version}")
        
        # Test database creation permissions
        print("3️⃣  Testing table creation permissions...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("   ✅ Table creation successful!")
        
        # Test insert
        print("4️⃣  Testing data insertion...")
        cursor.execute("""
            INSERT INTO connection_test (test_message) 
            VALUES ('Database connection test successful!');
        """)
        conn.commit()
        print("   ✅ Data insertion successful!")
        
        # Test select
        print("5️⃣  Testing data retrieval...")
        cursor.execute("SELECT test_message FROM connection_test ORDER BY created_at DESC LIMIT 1;")
        message = cursor.fetchone()[0]
        print(f"   ✅ Retrieved: {message}")
        
        # Clean up test table
        print("6️⃣  Cleaning up...")
        cursor.execute("DROP TABLE connection_test;")
        conn.commit()
        print("   ✅ Cleanup successful!")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print()
        print("🎉 Database connection test PASSED!")
        print("   Your RDS instance is ready for the Federal Budget Dashboard")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("🧪 Federal Budget Dashboard - Database Connection Test")
    print("=" * 55)
    print()
    
    success = test_connection()
    
    print()
    if success:
        print("✅ Ready for next steps:")
        print("   1. Run: python scripts/seed_database.py")
        print("   2. Start local server: python run_local.py")
        print("   3. Test API: python test_api.py")
    else:
        print("❌ Connection failed. Check:")
        print("   1. DATABASE_URL environment variable is set correctly")
        print("   2. RDS instance is running and accessible")
        print("   3. Security groups allow connections")
        print("   4. Your local IP has access (if connecting from outside AWS)")

if __name__ == "__main__":
    main() 
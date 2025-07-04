#!/usr/bin/env python3
"""
Test database connection script for Federal Budget Dashboard

This script tests the connection to the SQLite database
and verifies basic functionality.
"""

import os
import sys
import sqlite3
from urllib.parse import urlparse

def test_connection():
    """Test database connection and basic operations"""
    
    # Get database URL from environment or use default SQLite
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Default SQLite path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "..", "backend", "federal_budget.db")
        db_path = os.path.abspath(db_path)
        database_url = f"sqlite:///{db_path}"
        print(f"Using default SQLite database: {db_path}")
    
    try:
        # Parse the database URL
        parsed = urlparse(database_url)
        
        print("🔍 Testing database connection...")
        if parsed.scheme == "sqlite":
            db_path = parsed.path
            print(f"   Database file: {db_path}")
        else:
            print(f"   Host: {parsed.hostname}")
            print(f"   Port: {parsed.port}")
            print(f"   Database: {parsed.path[1:]}")  # Remove leading slash
            print(f"   User: {parsed.username}")
        print()
        
        # Test connection
        print("1️⃣  Connecting to database...")
        if parsed.scheme == "sqlite":
            conn = sqlite3.connect(parsed.path)
            cursor = conn.cursor()
        else:
            print("❌ Only SQLite is supported in Phase 1")
            return False
        
        print("   ✅ Connection successful!")
        
        # Test basic query
        print("2️⃣  Testing basic query...")
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()[0]
        print(f"   ✅ SQLite version: {version}")
        
        # Test database creation permissions
        print("3️⃣  Testing table creation permissions...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
        print("   Your SQLite database is ready for the Federal Budget Dashboard")
        return True
        
    except sqlite3.Error as e:
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
        print("   1. Database file permissions and path")
        print("   2. SQLite is properly installed") 
        print("   3. No file locks or permission issues")
        print("   4. DATABASE_URL format (if using custom database)")

if __name__ == "__main__":
    main() 
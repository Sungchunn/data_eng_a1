"""Test PostgreSQL database connection"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection and print server version"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5433'),
            database=os.getenv('DB_NAME', 'yelp'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )

        # Create cursor
        cursor = conn.cursor()

        # Execute test query
        cursor.execute('SELECT version();')
        db_version = cursor.fetchone()

        print("✅ Database connection successful!")
        print(f"PostgreSQL version: {db_version[0]}")

        # Close connections
        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == '__main__':
    test_connection()

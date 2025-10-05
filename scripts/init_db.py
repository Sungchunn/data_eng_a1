"""Initialize database schema - create tables and indexes"""
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5433'),
        database=os.getenv('DB_NAME', 'yelp'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )

def execute_sql_file(filepath: str, description: str = ""):
    """Execute SQL from file"""
    print(f"{'='*60}")
    print(f"Executing: {filepath}")
    if description:
        print(f"Description: {description}")
    print(f"{'='*60}")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        with open(filepath, 'r') as f:
            sql = f.read()

        cursor.execute(sql)
        conn.commit()
        print(f"✅ Successfully executed {filepath}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error executing {filepath}: {e}")
        raise

    finally:
        cursor.close()
        conn.close()

def verify_schema():
    """Verify tables and indexes created"""
    print(f"\n{'='*60}")
    print("Verifying Schema")
    print(f"{'='*60}")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Count tables
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"✅ Tables created: {table_count}")

        # Count indexes
        cursor.execute("""
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE schemaname = 'public'
        """)
        index_count = cursor.fetchone()[0]
        print(f"✅ Indexes created: {index_count}")

        # List tables
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        print(f"\nTables:")
        for table in tables:
            print(f"  - {table[0]}")

        # Check row counts
        cursor.execute("""
            SELECT
                'businesses' AS table_name, COUNT(*) AS row_count FROM businesses
            UNION ALL SELECT 'reviews', COUNT(*) FROM reviews
            UNION ALL SELECT 'users', COUNT(*) FROM users
            UNION ALL SELECT 'tips', COUNT(*) FROM tips
            UNION ALL SELECT 'checkins', COUNT(*) FROM checkins
        """)
        row_counts = cursor.fetchall()
        print(f"\nRow Counts:")
        for table_name, count in row_counts:
            print(f"  - {table_name}: {count:,}")

    finally:
        cursor.close()
        conn.close()

def main():
    """Main initialization function"""
    print("\n" + "="*60)
    print("DATABASE SCHEMA INITIALIZATION")
    print("="*60 + "\n")

    base_dir = Path(__file__).parent.parent

    # Step 1: Create tables
    execute_sql_file(
        base_dir / 'schema' / 'create_tables.sql',
        "Create all database tables"
    )

    # Step 2: Create indexes
    execute_sql_file(
        base_dir / 'schema' / 'create_indexes.sql',
        "Create all indexes and analyze tables"
    )

    # Step 3: Verify
    verify_schema()

    print(f"\n{'='*60}")
    print("✅ Database schema initialization complete!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()

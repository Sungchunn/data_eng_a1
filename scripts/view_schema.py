"""View database schema and table information"""
import psycopg2
import os
from dotenv import load_dotenv

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

def list_tables():
    """List all tables"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)

    tables = cursor.fetchall()

    print("\n" + "="*60)
    print("TABLES")
    print("="*60)
    for i, (table,) in enumerate(tables, 1):
        print(f"{i:2}. {table}")

    cursor.close()
    conn.close()

def table_info(table_name):
    """Show detailed table information"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get columns
    cursor.execute(f"""
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()

    print("\n" + "="*60)
    print(f"TABLE: {table_name}")
    print("="*60)
    print(f"{'Column':<25} {'Type':<20} {'Nullable':<10}")
    print("-"*60)

    for col_name, data_type, max_len, nullable in columns:
        if max_len:
            type_str = f"{data_type}({max_len})"
        else:
            type_str = data_type
        print(f"{col_name:<25} {type_str:<20} {nullable:<10}")

    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print("-"*60)
    print(f"Row count: {count:,}")

    cursor.close()
    conn.close()

def table_counts():
    """Show row counts for all tables"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            'businesses' AS table_name, COUNT(*) AS row_count FROM businesses
        UNION ALL SELECT 'business_categories', COUNT(*) FROM business_categories
        UNION ALL SELECT 'business_hours', COUNT(*) FROM business_hours
        UNION ALL SELECT 'business_attributes', COUNT(*) FROM business_attributes
        UNION ALL SELECT 'users', COUNT(*) FROM users
        UNION ALL SELECT 'user_friends', COUNT(*) FROM user_friends
        UNION ALL SELECT 'user_elite_years', COUNT(*) FROM user_elite_years
        UNION ALL SELECT 'reviews', COUNT(*) FROM reviews
        UNION ALL SELECT 'tips', COUNT(*) FROM tips
        UNION ALL SELECT 'checkins', COUNT(*) FROM checkins
    """)

    counts = cursor.fetchall()

    print("\n" + "="*60)
    print("ROW COUNTS")
    print("="*60)
    print(f"{'Table':<25} {'Rows':>15}")
    print("-"*60)

    total = 0
    for table, count in counts:
        print(f"{table:<25} {count:>15,}")
        total += count

    print("-"*60)
    print(f"{'TOTAL':<25} {total:>15,}")

    cursor.close()
    conn.close()

def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "tables":
            list_tables()
        elif command == "counts":
            table_counts()
        elif command == "info" and len(sys.argv) > 2:
            table_info(sys.argv[2])
        else:
            print("Usage:")
            print("  python scripts/view_schema.py tables          # List all tables")
            print("  python scripts/view_schema.py counts          # Show row counts")
            print("  python scripts/view_schema.py info <table>    # Show table details")
    else:
        # Default: show everything
        list_tables()
        table_counts()

if __name__ == '__main__':
    main()

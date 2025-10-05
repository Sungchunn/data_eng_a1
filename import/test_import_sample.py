"""
Test import with small sample (first 1000 rows)
Use this to verify import logic before running full import
"""

import json
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATASET_DIR = Path(__file__).parent.parent / 'yelp_dataset'
SAMPLE_SIZE = 1000

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5433'),
        database=os.getenv('DB_NAME', 'yelp'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )

def test_businesses():
    """Test business import with sample"""
    print("\nTesting business import (first 1000 rows)...")

    conn = get_connection()
    cursor = conn.cursor()

    filepath = DATASET_DIR / 'yelp_academic_dataset_business.json'
    business_batch = []
    category_batch = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= SAMPLE_SIZE:
                break

            record = json.loads(line)

            business_batch.append((
                record['business_id'],
                record.get('name'),
                record.get('address'),
                record.get('city'),
                record.get('state'),
                record.get('postal_code'),
                record.get('latitude'),
                record.get('longitude'),
                record.get('stars'),
                record.get('review_count', 0),
                record.get('is_open', 1)
            ))

            # Categories
            categories = record.get('categories')
            if categories:
                for category in categories.split(', '):
                    category_batch.append((
                        record['business_id'],
                        category.strip()
                    ))

    # Insert
    execute_batch(cursor, """
        INSERT INTO businesses
        (business_id, name, address, city, state, postal_code,
         latitude, longitude, stars, review_count, is_open)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (business_id) DO NOTHING
    """, business_batch)

    if category_batch:
        execute_batch(cursor, """
            INSERT INTO business_categories (business_id, category)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, category_batch)

    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM businesses")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print(f"✅ Imported {count} businesses")

def test_users():
    """Test user import with sample"""
    print("\nTesting user import (first 1000 rows)...")

    conn = get_connection()
    cursor = conn.cursor()

    filepath = DATASET_DIR / 'yelp_academic_dataset_user.json'
    user_batch = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= SAMPLE_SIZE:
                break

            record = json.loads(line)

            yelping_since = None
            if record.get('yelping_since'):
                try:
                    # Try with timestamp first
                    yelping_since = datetime.strptime(
                        record['yelping_since'], '%Y-%m-%d %H:%M:%S'
                    ).date()
                except ValueError:
                    # Fall back to date only
                    yelping_since = datetime.strptime(
                        record['yelping_since'], '%Y-%m-%d'
                    ).date()

            user_batch.append((
                record['user_id'],
                record.get('name'),
                record.get('review_count', 0),
                yelping_since,
                record.get('useful', 0),
                record.get('funny', 0),
                record.get('cool', 0),
                record.get('fans', 0),
                record.get('average_stars'),
                record.get('compliment_hot', 0),
                record.get('compliment_more', 0),
                record.get('compliment_profile', 0),
                record.get('compliment_cute', 0),
                record.get('compliment_list', 0),
                record.get('compliment_note', 0),
                record.get('compliment_plain', 0),
                record.get('compliment_cool', 0),
                record.get('compliment_funny', 0),
                record.get('compliment_writer', 0),
                record.get('compliment_photos', 0)
            ))

    # Insert
    execute_batch(cursor, """
        INSERT INTO users
        (user_id, name, review_count, yelping_since, useful, funny, cool, fans,
         average_stars, compliment_hot, compliment_more, compliment_profile,
         compliment_cute, compliment_list, compliment_note, compliment_plain,
         compliment_cool, compliment_funny, compliment_writer, compliment_photos)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    """, user_batch)

    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print(f"✅ Imported {count} users")

def show_counts():
    """Show current row counts"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            'businesses' AS table_name, COUNT(*) AS row_count FROM businesses
        UNION ALL SELECT 'business_categories', COUNT(*) FROM business_categories
        UNION ALL SELECT 'users', COUNT(*) FROM users
        UNION ALL SELECT 'reviews', COUNT(*) FROM reviews
        UNION ALL SELECT 'tips', COUNT(*) FROM tips
    """)

    results = cursor.fetchall()

    print(f"\n{'Table':<25} {'Rows':>10}")
    print("-"*37)
    for table, count in results:
        print(f"{table:<25} {count:>10,}")

    cursor.close()
    conn.close()

def main():
    """Run sample import test"""
    print("="*60)
    print("SAMPLE IMPORT TEST")
    print("="*60)

    test_businesses()
    test_users()
    show_counts()

    print("\n✅ Sample import test complete!")
    print("\nIf everything looks good, run full import with:")
    print("  poetry run python import/import_data.py")

if __name__ == '__main__':
    main()

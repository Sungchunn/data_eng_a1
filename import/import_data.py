"""
Import Yelp dataset into PostgreSQL database

This script imports all JSON files from the Yelp academic dataset into
the PostgreSQL database with proper transformations and batch processing.
"""

import json
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import os
from dotenv import load_dotenv
import sys
from io import StringIO
import csv

# Load environment variables
load_dotenv()

# Configuration
BATCH_SIZE = 50000  # Increased from 10000 for better performance
COPY_BATCH_SIZE = 100000  # For COPY operations (larger batches)
DATASET_DIR = Path(__file__).parent.parent / 'yelp_dataset'

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5433'),
        database=os.getenv('DB_NAME', 'yelp'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )

def count_lines(filepath):
    """Count total lines in file for progress bar"""
    print(f"Counting lines in {filepath.name}...")
    with open(filepath, 'rb') as f:
        return sum(1 for _ in f)

def import_businesses(filepath):
    """Import businesses from JSON file"""
    print("\n" + "="*60)
    print("IMPORTING BUSINESSES")
    print("="*60)

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    # Prepare batches
    business_batch = []
    category_batch = []
    hours_batch = []
    attributes_batch = []

    total_lines = count_lines(filepath)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Processing businesses"):
                record = json.loads(line)

                # Main business record
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

                # Categories (split comma-separated string)
                categories = record.get('categories')
                if categories:
                    for category in categories.split(', '):
                        category_batch.append((
                            record['business_id'],
                            category.strip()
                        ))

                # Hours
                hours = record.get('hours')
                if hours:
                    for day, time_range in hours.items():
                        hours_batch.append((
                            record['business_id'],
                            day,
                            time_range
                        ))

                # Attributes
                attributes = record.get('attributes')
                if attributes:
                    for attr_name, attr_value in attributes.items():
                        # Convert dicts to JSON strings
                        if isinstance(attr_value, dict):
                            value_str = json.dumps(attr_value)
                        else:
                            value_str = str(attr_value)

                        attributes_batch.append((
                            record['business_id'],
                            attr_name,
                            value_str
                        ))

                # Commit batches
                if len(business_batch) >= BATCH_SIZE:
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

                    if hours_batch:
                        execute_batch(cursor, """
                            INSERT INTO business_hours (business_id, day, hours)
                            VALUES (%s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, hours_batch)

                    if attributes_batch:
                        execute_batch(cursor, """
                            INSERT INTO business_attributes
                            (business_id, attribute_name, attribute_value)
                            VALUES (%s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, attributes_batch)

                    conn.commit()
                    business_batch = []
                    category_batch = []
                    hours_batch = []
                    attributes_batch = []

        # Final batch
        if business_batch:
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

            if hours_batch:
                execute_batch(cursor, """
                    INSERT INTO business_hours (business_id, day, hours)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, hours_batch)

            if attributes_batch:
                execute_batch(cursor, """
                    INSERT INTO business_attributes
                    (business_id, attribute_name, attribute_value)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, attributes_batch)

            conn.commit()

        cursor.close()
        conn.close()

        print("✅ Businesses imported successfully")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing businesses: {e}")
        raise

def import_users(filepath):
    """Import users from JSON file"""
    print("\n" + "="*60)
    print("IMPORTING USERS")
    print("="*60)

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    user_batch = []
    elite_batch = []

    total_lines = count_lines(filepath)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Processing users"):
                record = json.loads(line)

                # Parse yelping_since date
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

                # Main user record
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

                # Elite years
                elite = record.get('elite')
                if elite and elite != 'None' and elite:
                    # Handle both array and comma-separated string formats
                    if isinstance(elite, list):
                        years = elite
                    else:
                        years = [int(y) for y in str(elite).split(',') if y.strip().isdigit()]

                    for year in years:
                        if isinstance(year, int):
                            elite_batch.append((record['user_id'], year))

                # Commit batch
                if len(user_batch) >= BATCH_SIZE:
                    execute_batch(cursor, """
                        INSERT INTO users
                        (user_id, name, review_count, yelping_since, useful, funny, cool, fans,
                         average_stars, compliment_hot, compliment_more, compliment_profile,
                         compliment_cute, compliment_list, compliment_note, compliment_plain,
                         compliment_cool, compliment_funny, compliment_writer, compliment_photos)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO NOTHING
                    """, user_batch)

                    if elite_batch:
                        execute_batch(cursor, """
                            INSERT INTO user_elite_years (user_id, year)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """, elite_batch)

                    conn.commit()
                    user_batch = []
                    elite_batch = []

        # Final batch
        if user_batch:
            execute_batch(cursor, """
                INSERT INTO users
                (user_id, name, review_count, yelping_since, useful, funny, cool, fans,
                 average_stars, compliment_hot, compliment_more, compliment_profile,
                 compliment_cute, compliment_list, compliment_note, compliment_plain,
                 compliment_cool, compliment_funny, compliment_writer, compliment_photos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, user_batch)

            if elite_batch:
                execute_batch(cursor, """
                    INSERT INTO user_elite_years (user_id, year)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, elite_batch)

            conn.commit()

        cursor.close()
        conn.close()

        print("✅ Users imported successfully")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing users: {e}")
        raise

def import_user_friends(filepath):
    """Import user friendships - run after users are imported"""
    print("\n" + "="*60)
    print("IMPORTING USER FRIENDSHIPS")
    print("="*60)

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    # Pre-load all valid user IDs into a set for O(1) lookup
    print("Loading valid user IDs...")
    cursor.execute("SELECT user_id FROM users")
    valid_users = set(row[0] for row in cursor.fetchall())
    print(f"Loaded {len(valid_users):,} valid user IDs")

    friends_batch = []
    total_lines = count_lines(filepath)
    skipped = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Processing friendships"):
                record = json.loads(line)
                user_id = record['user_id']

                friends = record.get('friends')
                if friends and friends != 'None':
                    # Handle both array and comma-separated string
                    if isinstance(friends, list):
                        friend_list = friends
                    else:
                        friend_list = [f.strip() for f in friends.split(',') if f.strip()]

                    for friend_id in friend_list:
                        # Skip if either user doesn't exist (in-memory validation)
                        if user_id not in valid_users or friend_id not in valid_users:
                            skipped += 1
                            continue

                        # Store only one direction to avoid duplicates
                        if user_id < friend_id:
                            friends_batch.append((user_id, friend_id))
                        else:
                            friends_batch.append((friend_id, user_id))

                # Commit batch
                if len(friends_batch) >= BATCH_SIZE:
                    execute_batch(cursor, """
                        INSERT INTO user_friends (user_id, friend_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, friends_batch)
                    conn.commit()
                    friends_batch = []

        # Final batch
        if friends_batch:
            execute_batch(cursor, """
                INSERT INTO user_friends (user_id, friend_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, friends_batch)
            conn.commit()

        cursor.close()
        conn.close()

        print(f"✅ User friendships imported successfully (skipped {skipped:,} invalid friendships)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing friendships: {e}")
        raise

def import_reviews(filepath):
    """Import reviews from JSON file using COPY for maximum performance"""
    print("\n" + "="*60)
    print("IMPORTING REVIEWS (using COPY)")
    print("="*60)

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    # Pre-load valid user and business IDs to avoid FK violations
    print("Loading valid user IDs...")
    cursor.execute("SELECT user_id FROM users")
    valid_users = set(row[0] for row in cursor.fetchall())
    print(f"Loaded {len(valid_users):,} valid user IDs")

    print("Loading valid business IDs...")
    cursor.execute("SELECT business_id FROM businesses")
    valid_businesses = set(row[0] for row in cursor.fetchall())
    print(f"Loaded {len(valid_businesses):,} valid business IDs")

    total_lines = count_lines(filepath)
    buffer = StringIO()
    batch_count = 0
    total_imported = 0
    skipped = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Processing reviews"):
                record = json.loads(line)

                # Skip reviews with invalid user_id or business_id
                user_id = record.get('user_id')
                business_id = record.get('business_id')

                if not user_id or user_id not in valid_users:
                    skipped += 1
                    continue

                if not business_id or business_id not in valid_businesses:
                    skipped += 1
                    continue

                # Parse date (handle both date-only and datetime formats)
                date_str = record['date']
                try:
                    review_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    review_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()

                # Escape text for COPY (handle tabs, newlines, backslashes)
                text = record['text'].replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

                # Convert stars to integer (handle both int and float values)
                stars = int(float(record['stars']))

                # Write to buffer as tab-separated values
                buffer.write(f"{record['review_id']}\t{user_id}\t{business_id}\t"
                           f"{stars}\t{review_date}\t{text}\t"
                           f"{int(record.get('useful', 0))}\t{int(record.get('funny', 0))}\t{int(record.get('cool', 0))}\n")

                batch_count += 1

                # Use COPY for larger batches (more efficient)
                if batch_count >= COPY_BATCH_SIZE:
                    buffer.seek(0)
                    cursor.copy_from(buffer, 'reviews',
                                   columns=['review_id', 'user_id', 'business_id', 'stars', 'date',
                                           'text', 'useful', 'funny', 'cool'])
                    conn.commit()
                    total_imported += batch_count
                    batch_count = 0
                    buffer = StringIO()

        # Final batch
        if batch_count > 0:
            buffer.seek(0)
            cursor.copy_from(buffer, 'reviews',
                           columns=['review_id', 'user_id', 'business_id', 'stars', 'date',
                                   'text', 'useful', 'funny', 'cool'])
            conn.commit()
            total_imported += batch_count

        cursor.close()
        conn.close()

        print(f"✅ Reviews imported successfully ({total_imported:,} reviews, skipped {skipped:,} invalid references)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing reviews: {e}")
        raise

def import_tips(filepath):
    """Import tips from JSON file"""
    print("\n" + "="*60)
    print("IMPORTING TIPS")
    print("="*60)

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    # Pre-load valid user and business IDs
    print("Loading valid user IDs...")
    cursor.execute("SELECT user_id FROM users")
    valid_users = set(row[0] for row in cursor.fetchall())
    print(f"Loaded {len(valid_users):,} valid user IDs")

    print("Loading valid business IDs...")
    cursor.execute("SELECT business_id FROM businesses")
    valid_businesses = set(row[0] for row in cursor.fetchall())
    print(f"Loaded {len(valid_businesses):,} valid business IDs")

    tip_batch = []
    total_lines = count_lines(filepath)
    skipped = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Processing tips"):
                record = json.loads(line)

                # Skip tips with invalid user_id or business_id
                user_id = record.get('user_id')
                business_id = record.get('business_id')

                if not user_id or user_id not in valid_users:
                    skipped += 1
                    continue

                if not business_id or business_id not in valid_businesses:
                    skipped += 1
                    continue

                # Parse date (handle both date-only and datetime formats)
                date_str = record['date']
                try:
                    tip_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    tip_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()

                tip_batch.append((
                    user_id,
                    business_id,
                    record['text'],
                    tip_date,
                    record.get('compliment_count', 0)
                ))

                # Commit batch
                if len(tip_batch) >= BATCH_SIZE:
                    execute_batch(cursor, """
                        INSERT INTO tips (user_id, business_id, text, date, compliment_count)
                        VALUES (%s, %s, %s, %s, %s)
                    """, tip_batch)
                    conn.commit()
                    tip_batch = []

        # Final batch
        if tip_batch:
            execute_batch(cursor, """
                INSERT INTO tips (user_id, business_id, text, date, compliment_count)
                VALUES (%s, %s, %s, %s, %s)
            """, tip_batch)
            conn.commit()

        cursor.close()
        conn.close()

        print(f"✅ Tips imported successfully (skipped {skipped:,} invalid references)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing tips: {e}")
        raise

def import_checkins(filepath):
    """Import checkins from JSON file"""
    print("\n" + "="*60)
    print("IMPORTING CHECKINS")
    print("="*60)

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    # Pre-load valid business IDs
    print("Loading valid business IDs...")
    cursor.execute("SELECT business_id FROM businesses")
    valid_businesses = set(row[0] for row in cursor.fetchall())
    print(f"Loaded {len(valid_businesses):,} valid business IDs")

    checkin_batch = []
    total_lines = count_lines(filepath)
    skipped = 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Processing checkins"):
                record = json.loads(line)
                business_id = record.get('business_id')

                # Skip checkins with invalid business_id
                if not business_id or business_id not in valid_businesses:
                    skipped += 1
                    continue

                # Parse comma-separated timestamps
                date_str = record.get('date', '')
                if date_str:
                    timestamps = [ts.strip() for ts in date_str.split(',') if ts.strip()]

                    for ts in timestamps:
                        try:
                            dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                            checkin_batch.append((business_id, dt))
                        except:
                            continue

                # Commit batch
                if len(checkin_batch) >= BATCH_SIZE:
                    execute_batch(cursor, """
                        INSERT INTO checkins (business_id, checkin_time)
                        VALUES (%s, %s)
                    """, checkin_batch)
                    conn.commit()
                    checkin_batch = []

        # Final batch
        if checkin_batch:
            execute_batch(cursor, """
                INSERT INTO checkins (business_id, checkin_time)
                VALUES (%s, %s)
            """, checkin_batch)
            conn.commit()

        cursor.close()
        conn.close()

        print(f"✅ Checkins imported successfully (skipped {skipped:,} invalid references)")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing checkins: {e}")
        raise

def verify_import():
    """Verify data was imported correctly"""
    print("\n" + "="*60)
    print("VERIFYING IMPORT")
    print("="*60)

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

    results = cursor.fetchall()

    print(f"\n{'Table':<25} {'Rows':>15}")
    print("-"*42)

    total = 0
    for table, count in results:
        print(f"{table:<25} {count:>15,}")
        total += count

    print("-"*42)
    print(f"{'TOTAL':<25} {total:>15,}")

    cursor.close()
    conn.close()

def main():
    """Main import function"""
    start_time = datetime.now()

    print("\n" + "="*60)
    print("YELP DATASET IMPORT")
    print("="*60)
    print(f"Start time: {start_time}")
    print(f"Dataset directory: {DATASET_DIR}")
    print(f"Batch size: {BATCH_SIZE:,}")

    # Check dataset directory exists
    if not DATASET_DIR.exists():
        print(f"\n❌ Error: Dataset directory not found: {DATASET_DIR}")
        print("Please download the Yelp dataset and place it in the 'yelp_dataset' directory")
        sys.exit(1)

    # Import order matters due to foreign key constraints
    files = {
        'businesses': DATASET_DIR / 'yelp_academic_dataset_business.json',
        'users': DATASET_DIR / 'yelp_academic_dataset_user.json',
        'reviews': DATASET_DIR / 'yelp_academic_dataset_review.json',
        'tips': DATASET_DIR / 'yelp_academic_dataset_tip.json',
        'checkins': DATASET_DIR / 'yelp_academic_dataset_checkin.json',
    }

    # Check all files exist
    for name, filepath in files.items():
        if not filepath.exists():
            print(f"\n❌ Error: {name} file not found: {filepath}")
            sys.exit(1)

    try:
        # Phase 1: Independent tables
        import_businesses(files['businesses'])
        import_users(files['users'])

        # Phase 2: User friendships (after users)
        import_user_friends(files['users'])

        # Phase 3: Dependent tables
        import_reviews(files['reviews'])
        import_tips(files['tips'])
        import_checkins(files['checkins'])

        # Verify
        verify_import()

        end_time = datetime.now()
        duration = end_time - start_time

        print("\n" + "="*60)
        print("✅ IMPORT COMPLETE")
        print("="*60)
        print(f"Start time: {start_time}")
        print(f"End time: {end_time}")
        print(f"Duration: {duration}")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

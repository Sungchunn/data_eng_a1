# Data Import Guide

> **⚠️ IMPORTANT - GIT POLICY:**
> - **NEVER commit the dataset files** to the repository
> - Dataset is located in `yelp_dataset/` (~9GB total)
> - This directory is excluded in `.gitignore`
> - Only commit the import scripts, NOT the data

## Overview
This guide covers importing the Yelp JSON dataset into PostgreSQL efficiently.

## Dataset Location
- Files are in: `/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1/yelp_dataset/`
- Total size: ~9GB (5 JSON files)
- Format: Newline-delimited JSON (one object per line)

## Import Strategy

### 1. Prerequisites
- PostgreSQL database running (via Docker Compose)
- Schema tables created (`create_tables.sql`)
- Python with required dependencies (psycopg2, poetry)

### 2. Import Order
Dependencies require specific order:

1. **Independent tables** (can run in parallel):
   - `businesses`
   - `users`

2. **Dependent on businesses**:
   - `business_categories`
   - `business_hours`
   - `business_attributes`
   - `reviews` (also needs users)
   - `tips` (also needs users)
   - `checkins`

3. **Dependent on users**:
   - `user_friends` (needs all users loaded first)
   - `user_elite_years`

### 3. Performance Optimization

#### Use COPY for Bulk Inserts
PostgreSQL's `COPY` command is 100x faster than INSERT:

```python
import psycopg2
from io import StringIO

# Generate CSV in memory
buffer = StringIO()
for record in records:
    buffer.write(f"{record['id']}\t{record['name']}\n")
buffer.seek(0)

# Bulk copy
cursor.copy_from(buffer, 'table_name', columns=['id', 'name'], sep='\t')
```

#### Disable Indexes During Import
```sql
-- Drop indexes (keep primary keys)
DROP INDEX IF EXISTS idx_businesses_location;
DROP INDEX IF EXISTS idx_reviews_business_date;
-- ... (all non-PK indexes)

-- Import data here

-- Recreate indexes
\i schema/create_indexes.sql
```

#### Batch Processing
- Process 10,000 rows per transaction
- Commit after each batch
- Show progress updates

### 4. Data Transformation

#### Business Categories (Array → Rows)
```python
# Original: "categories": "Mexican, Burgers, Gastropubs"
# Target: 3 rows in business_categories

categories = record['categories'].split(', ') if record['categories'] else []
for category in categories:
    rows.append((business_id, category.strip()))
```

#### Business Hours (Object → Rows)
```python
# Original: "hours": {"Monday": "10:00-22:00", "Tuesday": "10:00-22:00"}
# Target: 7 rows in business_hours (one per day)

hours = record.get('hours') or {}
for day, time_range in hours.items():
    rows.append((business_id, day, time_range))
```

#### Business Attributes (Object → Rows)
```python
# Original: "attributes": {"RestaurantsTakeOut": "True", "BusinessParking": {...}}
# Target: N rows in business_attributes

import json

attributes = record.get('attributes') or {}
for attr_name, attr_value in attributes.items():
    # Convert nested objects to JSON string
    if isinstance(attr_value, dict):
        value_str = json.dumps(attr_value)
    else:
        value_str = str(attr_value)
    rows.append((business_id, attr_name, value_str))
```

#### User Friends (Array → Rows)
```python
# Original: "friends": ["user1", "user2", "user3"]
# Target: 3 rows in user_friends

friends = record.get('friends', [])
for friend_id in friends:
    # Avoid duplicate edges (store only user_id < friend_id)
    if user_id < friend_id:
        rows.append((user_id, friend_id))
    elif friend_id < user_id:
        rows.append((friend_id, user_id))
```

#### Checkin Timestamps (CSV → Rows)
```python
# Original: "date": "2016-04-26 19:49:16, 2016-08-30 18:36:57, ..."
# Target: N rows in checkins

from datetime import datetime

date_str = record.get('date', '')
timestamps = [ts.strip() for ts in date_str.split(',') if ts.strip()]
for ts in timestamps:
    dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    rows.append((business_id, dt))
```

### 5. Error Handling

#### Missing/NULL Values
```python
def safe_get(record, key, default=None):
    """Get value from record, handling None and empty strings"""
    value = record.get(key)
    if value is None or value == '':
        return default
    return value

# Usage:
latitude = safe_get(record, 'latitude', None)  # Allow NULL
name = safe_get(record, 'name', 'Unknown')     # Default value
```

#### Data Validation
```python
def validate_business(record):
    """Validate required fields"""
    if not record.get('business_id'):
        raise ValueError("Missing business_id")
    if len(record['business_id']) != 22:
        raise ValueError(f"Invalid business_id length: {record['business_id']}")
    # Add more validations...
```

#### Foreign Key Violations
- Import in dependency order
- Skip orphaned records or create placeholder entities
- Log skipped records for review

### 6. Import Script Structure

```python
import json
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="yelp",
    user="postgres",
    password="postgres"
)
conn.autocommit = False

def import_businesses(filepath):
    """Import businesses from JSON file"""
    cursor = conn.cursor()
    batch = []
    batch_size = 10000

    with open(filepath, 'r') as f:
        for i, line in enumerate(f, 1):
            record = json.loads(line)

            # Extract main business fields
            row = (
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
            )
            batch.append(row)

            # Commit batch
            if len(batch) >= batch_size:
                execute_batch(cursor, """
                    INSERT INTO businesses
                    (business_id, name, address, city, state, postal_code,
                     latitude, longitude, stars, review_count, is_open)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, batch)
                conn.commit()
                print(f"Imported {i} businesses...")
                batch = []

        # Final batch
        if batch:
            execute_batch(cursor, """...""", batch)
            conn.commit()

    cursor.close()
    print(f"Completed: {i} businesses imported")

# Run imports
dataset_dir = Path('yelp_dataset')
import_businesses(dataset_dir / 'yelp_academic_dataset_business.json')
# ... more imports

conn.close()
```

### 7. Progress Tracking

Add logging and progress indicators:

```python
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Count lines for progress bar
def count_lines(filepath):
    with open(filepath, 'rb') as f:
        return sum(1 for _ in f)

# Use tqdm for progress
total_lines = count_lines(filepath)
with open(filepath, 'r') as f:
    for line in tqdm(f, total=total_lines, desc="Importing businesses"):
        # ... process line
```

### 8. Verification Queries

After import, verify data integrity:

```sql
-- Check row counts
SELECT 'businesses' AS table_name, COUNT(*) FROM businesses
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'users', COUNT(*) FROM users;

-- Check for orphaned foreign keys
SELECT COUNT(*) FROM reviews r
LEFT JOIN businesses b ON r.business_id = b.business_id
WHERE b.business_id IS NULL;

-- Check data quality
SELECT
    COUNT(*) AS total,
    COUNT(DISTINCT city) AS unique_cities,
    COUNT(DISTINCT state) AS unique_states,
    AVG(stars) AS avg_rating
FROM businesses;
```

### 9. Estimated Import Time

With optimizations (COPY, batching, no indexes):
- businesses: ~30 seconds
- users: ~2 minutes
- reviews: ~10-15 minutes
- categories: ~1 minute
- checkins: ~5 minutes
- **Total: ~20-25 minutes**

Without optimizations (individual INSERTs):
- **Total: 4-6 hours** (200x slower)

### 10. Common Issues

**Issue:** "duplicate key value violates unique constraint"
- **Cause:** Re-running import without clearing tables
- **Fix:** `TRUNCATE TABLE businesses CASCADE;` before re-import

**Issue:** "null value in column violates not-null constraint"
- **Cause:** Missing required field in JSON
- **Fix:** Add validation and default values

**Issue:** Out of memory
- **Cause:** Loading entire file into memory
- **Fix:** Process line-by-line (streaming)

**Issue:** Slow import
- **Cause:** Indexes enabled, small batches, autocommit
- **Fix:** Drop indexes, use batch_size=10000, disable autocommit

## Next Steps

1. Implement `import_data.py` script
2. Test with small subset (first 1000 rows)
3. Run full import with progress tracking
4. Verify data with SQL queries
5. Create indexes (`create_indexes.sql`)
6. Proceed to query implementation phase

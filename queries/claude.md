# Query Implementation Guide

> **⚠️ IMPORTANT - GIT POLICY:**
> - **NEVER commit database files or query results** with large datasets
> - Only commit the query implementation code (`query_functions.py`)
> - Test results can be documented in markdown but not raw data dumps

## Overview
This guide covers implementing the 5 required query functions for the Yelp dataset analysis.

## Requirements

### General Rules
1. **Single SQL query per question** (subqueries and CTEs allowed)
2. **Top-k queries must fetch exactly k rows** (use `LIMIT k`)
3. **Query execution time < 1 second** (with proper indexes)
4. **Well-documented code** (docstrings, comments, type hints)
5. **Reproducible** (can be run multiple times with same results)

### Query Functions Structure

```python
import psycopg2
from typing import List, Tuple, Dict, Any
from datetime import datetime

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="yelp",
        user="postgres",
        password="postgres"
    )

def query_1_top_rated_businesses(
    city: str,
    category: str,
    k: int = 10
) -> List[Tuple[str, str, float, int]]:
    """
    Find top k highest-rated businesses in a city for a specific category.

    Args:
        city: City name (e.g., "Philadelphia")
        category: Business category (e.g., "Restaurants")
        k: Number of results to return

    Returns:
        List of tuples: (business_id, name, stars, review_count)
        Sorted by stars DESC, review_count DESC

    Query pattern: Location + Category filter, Top-K sort
    Indexes used: idx_businesses_location, idx_business_categories_category
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            b.business_id,
            b.name,
            b.stars,
            b.review_count
        FROM businesses b
        JOIN business_categories bc ON b.business_id = bc.business_id
        WHERE b.city = %s
            AND bc.category = %s
            AND b.is_open = 1
        ORDER BY b.stars DESC, b.review_count DESC
        LIMIT %s
    """

    cursor.execute(query, (city, category, k))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results
```

## Query Examples

### 1. Top-Rated Businesses (Location + Category)

**Goal:** Find best restaurants in a city

**SQL Pattern:**
- JOIN between businesses and categories
- WHERE clause filters by city and category
- ORDER BY stars (primary), review_count (tiebreaker)
- LIMIT k for top-k

**Optimization:**
- Uses `idx_businesses_location` for city filter
- Uses `idx_business_categories_category` for category filter
- Uses `idx_businesses_stars` for sorting

### 2. Most Active Users (Aggregation)

**Goal:** Find users who have written the most reviews

```python
def query_2_most_active_users(k: int = 100) -> List[Tuple[str, str, int, int]]:
    """
    Find top k most active users by review count.

    Returns:
        List of tuples: (user_id, name, review_count, fans)
        Sorted by review_count DESC
    """
    query = """
        SELECT
            user_id,
            name,
            review_count,
            fans
        FROM users
        ORDER BY review_count DESC
        LIMIT %s
    """
```

**Optimization:**
- Direct table scan (no joins)
- Uses `idx_users_review_count` for sorting
- Very fast (<10ms)

### 3. Recent Reviews for Business (Temporal Query)

**Goal:** Get most recent reviews for a specific business

```python
def query_3_recent_reviews(
    business_id: str,
    k: int = 20
) -> List[Tuple[str, str, int, str, str]]:
    """
    Get k most recent reviews for a business.

    Returns:
        List of tuples: (review_id, user_name, stars, date, text_preview)
        Sorted by date DESC
    """
    query = """
        SELECT
            r.review_id,
            u.name AS user_name,
            r.stars,
            r.date,
            LEFT(r.text, 200) AS text_preview
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.business_id = %s
        ORDER BY r.date DESC
        LIMIT %s
    """
```

**Optimization:**
- Uses `idx_reviews_business_date` composite index
- Index-only scan possible (covering index)
- JOIN to users via primary key (very fast)

### 4. Friend Recommendations (Graph Query)

**Goal:** Find friend-of-friend recommendations

```python
def query_4_friend_recommendations(
    user_id: str,
    k: int = 10
) -> List[Tuple[str, str, int, int]]:
    """
    Recommend users who are friends of your friends but not your friend yet.

    Returns:
        List of tuples: (user_id, name, mutual_friends_count, fans)
        Sorted by mutual_friends_count DESC, fans DESC
    """
    query = """
        WITH my_friends AS (
            SELECT friend_id
            FROM user_friends
            WHERE user_id = %s
        ),
        friends_of_friends AS (
            SELECT
                uf.friend_id,
                COUNT(*) AS mutual_friends_count
            FROM user_friends uf
            WHERE uf.user_id IN (SELECT friend_id FROM my_friends)
                AND uf.friend_id != %s
                AND uf.friend_id NOT IN (SELECT friend_id FROM my_friends)
            GROUP BY uf.friend_id
        )
        SELECT
            u.user_id,
            u.name,
            fof.mutual_friends_count,
            u.fans
        FROM friends_of_friends fof
        JOIN users u ON fof.friend_id = u.user_id
        ORDER BY fof.mutual_friends_count DESC, u.fans DESC
        LIMIT %s
    """
```

**Optimization:**
- Uses CTE for readability
- Uses `user_friends_pkey` and `idx_user_friends_friend_id`
- Aggregation (COUNT) on intermediate results
- May be slower for users with many friends (>1000)

### 5. Popular Check-in Times (Time Series)

**Goal:** Find most popular check-in hours for a business

```python
def query_5_popular_checkin_times(
    business_id: str,
    k: int = 10
) -> List[Tuple[int, int]]:
    """
    Find the k most popular check-in hours for a business.

    Returns:
        List of tuples: (hour_of_day, checkin_count)
        Sorted by checkin_count DESC
    """
    query = """
        SELECT
            EXTRACT(HOUR FROM checkin_time) AS hour_of_day,
            COUNT(*) AS checkin_count
        FROM checkins
        WHERE business_id = %s
        GROUP BY hour_of_day
        ORDER BY checkin_count DESC
        LIMIT %s
    """
```

**Optimization:**
- Uses `idx_checkins_business_id` for filtering
- GROUP BY on extracted hour
- Aggregation on potentially large result set

## Advanced Query Patterns

### Full-Text Search

```python
def query_search_reviews(
    keywords: str,
    min_stars: int = 4,
    k: int = 50
) -> List[Tuple[str, str, str, float]]:
    """
    Search reviews by keywords with full-text search.

    Args:
        keywords: Space-separated search terms
        min_stars: Minimum star rating filter
        k: Number of results

    Returns:
        List of tuples: (review_id, business_name, text_snippet, rank)
    """
    query = """
        SELECT
            r.review_id,
            b.name AS business_name,
            ts_headline('english', r.text, query) AS snippet,
            ts_rank(to_tsvector('english', r.text), query) AS rank
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id,
        to_tsquery('english', %s) AS query
        WHERE to_tsvector('english', r.text) @@ query
            AND r.stars >= %s
        ORDER BY rank DESC
        LIMIT %s
    """
```

### Geospatial Proximity

```python
def query_nearby_businesses(
    latitude: float,
    longitude: float,
    radius_miles: float = 5.0,
    k: int = 20
) -> List[Tuple[str, str, float]]:
    """
    Find businesses within radius of a point.

    Uses Haversine formula for distance calculation.
    """
    query = """
        SELECT
            business_id,
            name,
            (
                3959 * acos(
                    cos(radians(%s)) *
                    cos(radians(latitude)) *
                    cos(radians(longitude) - radians(%s)) +
                    sin(radians(%s)) *
                    sin(radians(latitude))
                )
            ) AS distance_miles
        FROM businesses
        WHERE latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND is_open = 1
        HAVING distance_miles <= %s
        ORDER BY distance_miles ASC
        LIMIT %s
    """
    # Note: For better performance, use PostGIS extension
```

### Temporal Aggregation

```python
def query_review_trends(
    business_id: str,
    start_date: str = '2020-01-01'
) -> List[Tuple[str, int, float]]:
    """
    Analyze review trends over time (monthly aggregation).

    Returns:
        List of tuples: (month, review_count, avg_stars)
    """
    query = """
        SELECT
            TO_CHAR(date, 'YYYY-MM') AS month,
            COUNT(*) AS review_count,
            AVG(stars) AS avg_stars
        FROM reviews
        WHERE business_id = %s
            AND date >= %s
        GROUP BY month
        ORDER BY month ASC
    """
```

## Performance Testing

### Timing Decorator

```python
import time
from functools import wraps

def time_query(func):
    """Decorator to measure query execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} completed in {elapsed:.4f}s")
        return result
    return wrapper

@time_query
def query_1_top_rated_businesses(...):
    # ... implementation
```

### EXPLAIN ANALYZE

```python
def explain_query(query: str, params: tuple):
    """Show query execution plan"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"EXPLAIN ANALYZE {query}", params)
    plan = cursor.fetchall()

    cursor.close()
    conn.close()

    for line in plan:
        print(line[0])
```

### Benchmark Suite

```python
def benchmark_all_queries():
    """Run all queries and measure performance"""
    results = {}

    # Query 1
    start = time.perf_counter()
    query_1_top_rated_businesses('Philadelphia', 'Restaurants', 10)
    results['query_1'] = time.perf_counter() - start

    # Query 2
    start = time.perf_counter()
    query_2_most_active_users(100)
    results['query_2'] = time.perf_counter() - start

    # ... more queries

    # Report
    print("\nQuery Performance Report:")
    print("-" * 40)
    for name, elapsed in results.items():
        status = "✓" if elapsed < 1.0 else "✗"
        print(f"{status} {name}: {elapsed:.4f}s")
```

## Testing

### Unit Tests

```python
import unittest

class TestQueryFunctions(unittest.TestCase):
    def test_query_1_returns_k_results(self):
        """Verify top-k query returns exactly k results"""
        k = 5
        results = query_1_top_rated_businesses('Philadelphia', 'Restaurants', k)
        self.assertEqual(len(results), k)

    def test_query_1_sorted_correctly(self):
        """Verify results are sorted by stars DESC"""
        results = query_1_top_rated_businesses('Philadelphia', 'Restaurants', 10)
        stars = [r[2] for r in results]
        self.assertEqual(stars, sorted(stars, reverse=True))

    def test_query_performance(self):
        """Verify query completes in under 1 second"""
        start = time.perf_counter()
        query_1_top_rated_businesses('Philadelphia', 'Restaurants', 10)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 1.0)
```

## Common Pitfalls

### 1. Not Using Indexes

**Problem:**
```sql
-- Full table scan (slow)
SELECT * FROM reviews WHERE date > '2020-01-01';
```

**Solution:**
```sql
-- Uses idx_reviews_date
SELECT * FROM reviews WHERE date > '2020-01-01';
-- Verify with EXPLAIN
```

### 2. SELECT * Instead of Specific Columns

**Problem:**
```sql
-- Fetches unnecessary data
SELECT * FROM reviews WHERE business_id = 'abc123';
```

**Solution:**
```sql
-- Only fetch needed columns
SELECT review_id, stars, date, text FROM reviews WHERE business_id = 'abc123';
```

### 3. Not Using LIMIT for Top-K

**Problem:**
```python
# Fetches all results, sorts in Python
results = cursor.fetchall()
results.sort(key=lambda x: x[2], reverse=True)
return results[:k]
```

**Solution:**
```sql
-- Let database handle sorting and limiting
SELECT ... ORDER BY stars DESC LIMIT %s
```

### 4. N+1 Query Problem

**Problem:**
```python
# One query per business (very slow)
for business_id in business_ids:
    cursor.execute("SELECT * FROM reviews WHERE business_id = %s", (business_id,))
```

**Solution:**
```python
# Single query with IN clause
cursor.execute("SELECT * FROM reviews WHERE business_id = ANY(%s)", (business_ids,))
```

## Documentation Requirements

Each query function must have:

1. **Docstring** with:
   - Purpose description
   - Parameter types and descriptions
   - Return type and format
   - Example usage

2. **Inline comments** explaining:
   - Complex SQL logic
   - Index usage
   - Performance considerations

3. **Type hints**:
   ```python
   def query_func(param: str, k: int = 10) -> List[Tuple[str, int]]:
   ```

## Next Steps

1. Implement all 5 query functions in `query_functions.py`
2. Add timing decorators
3. Test with various inputs
4. Verify execution time < 1 second
5. Document index usage for each query
6. Proceed to ablation study phase

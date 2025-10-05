# Index Documentation

## Overview
This document explains the indexing strategy for the Yelp dataset schema, including rationale, performance implications, and maintenance guidelines.

## Index Types in PostgreSQL

### 1. B-tree (Default)
**Use Cases:**
- Equality comparisons (`=`)
- Range queries (`<`, `>`, `BETWEEN`)
- Sorting (`ORDER BY`)
- Pattern matching (`LIKE 'prefix%'`)

**Characteristics:**
- Balanced tree structure
- Logarithmic lookup time O(log n)
- Supports index-only scans

### 2. GIN (Generalized Inverted Index)
**Use Cases:**
- Full-text search (tsvector)
- JSONB queries
- Array containment (`@>`, `<@`)

**Characteristics:**
- Inverted index structure
- Larger index size
- Slower updates, faster searches

### 3. Hash
**Use Cases:**
- Equality comparisons only
- Rarely used (B-tree usually better)

### 4. GiST (Generalized Search Tree)
**Use Cases:**
- Geometric data
- Full-text search (less efficient than GIN)
- Range types

## Index Inventory

### Business Table Indexes

| Index Name | Columns | Type | Purpose | Query Pattern |
|------------|---------|------|---------|---------------|
| `businesses_pkey` | business_id | B-tree | Primary key | Exact lookups |
| `idx_businesses_location` | city, state | B-tree | Location filter | `WHERE city = ? AND state = ?` |
| `idx_businesses_stars` | stars DESC | B-tree | Rating sort | `ORDER BY stars DESC` |
| `idx_businesses_is_open` | is_open | Partial B-tree | Open businesses | `WHERE is_open = 1` |
| `idx_businesses_coordinates` | latitude, longitude | B-tree | Proximity | Distance calculations |
| `idx_businesses_review_count` | review_count DESC | B-tree | Popularity sort | `ORDER BY review_count DESC` |

**Composite Index Considerations:**

`idx_businesses_location (city, state)`:
- Supports queries filtering by city alone (leftmost prefix)
- Does NOT support queries filtering by state alone
- Optimal for city-state pairs

**Partial Index Benefits:**

`idx_businesses_is_open WHERE is_open = 1`:
- Only indexes open businesses (reduces index size by ~50%)
- Not used for `WHERE is_open = 0` queries
- Significant space savings

### Business Category Indexes

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `business_categories_pkey` | business_id, category | B-tree | Primary key |
| `idx_business_categories_category` | category | B-tree | Reverse lookup |

**Query Optimization:**

Finding businesses by category:
```sql
SELECT b.*
FROM businesses b
JOIN business_categories bc ON b.business_id = bc.business_id
WHERE bc.category = 'Restaurants';
```
- Uses `idx_business_categories_category` to find business IDs
- Joins using `businesses_pkey`

### User Table Indexes

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `users_pkey` | user_id | B-tree | Primary key |
| `idx_users_review_count` | review_count DESC | B-tree | Top reviewers |
| `idx_users_fans` | fans DESC | B-tree | Influential users |
| `idx_users_yelping_since` | yelping_since | B-tree | Cohort analysis |
| `idx_users_average_stars` | average_stars | B-tree | Rating distribution |

**DESC Indexes:**

Indexes with `DESC` order:
- Optimized for `ORDER BY column DESC`
- Reverse scans are possible but less efficient
- Use when descending order is primary use case

### User Friends Indexes

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `user_friends_pkey` | user_id, friend_id | B-tree | Primary key |
| `idx_user_friends_friend_id` | friend_id | B-tree | Reverse lookup |

**Bidirectional Queries:**

Primary key supports:
```sql
-- Find all friends of user A
SELECT friend_id FROM user_friends WHERE user_id = 'A';
```

Secondary index supports:
```sql
-- Find all users who are friends with user B
SELECT user_id FROM user_friends WHERE friend_id = 'B';
```

### Review Table Indexes

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `reviews_pkey` | review_id | B-tree | Primary key |
| `idx_reviews_business_id` | business_id | B-tree | Business reviews |
| `idx_reviews_user_id` | user_id | B-tree | User reviews |
| `idx_reviews_date` | date | B-tree | Temporal queries |
| `idx_reviews_business_date` | business_id, date DESC | B-tree | Recent reviews |
| `idx_reviews_stars` | stars | B-tree | Rating analysis |
| `idx_reviews_useful` | useful DESC | B-tree | Top reviews |
| `idx_reviews_text_fts` | text (tsvector) | GIN | Full-text search |

**Composite Index Analysis:**

`idx_reviews_business_date (business_id, date DESC)`:

Supports:
- `WHERE business_id = ? ORDER BY date DESC` (optimal)
- `WHERE business_id = ? AND date > ?` (optimal)
- `WHERE business_id = ?` (uses index)

Does NOT support:
- `WHERE date > ?` alone (would need separate index)
- `ORDER BY date DESC` without business_id filter

**Full-Text Search:**

`idx_reviews_text_fts`:
```sql
CREATE INDEX idx_reviews_text_fts ON reviews
USING GIN(to_tsvector('english', text));

-- Usage:
SELECT * FROM reviews
WHERE to_tsvector('english', text) @@ to_tsquery('english', 'great & food');
```

**Trade-offs:**
- Index size: ~50% of text column size
- Insert/update overhead: 10-20% slower
- Query speedup: 100-1000x for text searches

### Tip and Checkin Indexes

| Table | Index Name | Columns | Purpose |
|-------|------------|---------|---------|
| tips | `idx_tips_business_id` | business_id | Business tips |
| tips | `idx_tips_user_id` | user_id | User tips |
| tips | `idx_tips_date` | date | Temporal |
| tips | `idx_tips_compliment_count` | compliment_count DESC | Top tips |
| checkins | `idx_checkins_business_id` | business_id | Business checkins |
| checkins | `idx_checkins_time` | checkin_time | Temporal |
| checkins | `idx_checkins_business_time` | business_id, checkin_time | Patterns |

## Index Size Estimates

Based on typical Yelp dataset sizes:

| Table | Rows | Table Size | Index Size | Total Size |
|-------|------|------------|------------|------------|
| businesses | 150K | 50 MB | 30 MB | 80 MB |
| business_categories | 500K | 25 MB | 20 MB | 45 MB |
| users | 2M | 400 MB | 150 MB | 550 MB |
| user_friends | 5M | 200 MB | 200 MB | 400 MB |
| reviews | 7M | 5 GB | 2 GB | 7 GB |
| tips | 1M | 300 MB | 100 MB | 400 MB |
| checkins | 3M | 150 MB | 100 MB | 250 MB |
| **Total** | **~18M** | **~6 GB** | **~2.6 GB** | **~8.6 GB** |

**Notes:**
- Index size is typically 30-50% of table size
- Full-text indexes can be 50-100% of text column size
- JSONB GIN indexes can be larger than data

## Performance Benchmarks

### Query Response Time Targets

| Query Type | Without Index | With Index | Target |
|------------|---------------|------------|--------|
| Primary key lookup | 100ms | <1ms | <1ms |
| Foreign key join | 500ms | 5ms | <10ms |
| Range scan (10% rows) | 2000ms | 50ms | <100ms |
| Full-text search | 10000ms | 100ms | <500ms |
| Top-k (k=10) | 5000ms | 10ms | <100ms |

### Index vs. Sequential Scan Breakpoint

PostgreSQL planner chooses index when:
- Selectivity < 5-10% of table rows
- Cost of index scan < cost of sequential scan

Example:
- Table: 1M rows
- Query: `WHERE stars >= 4.5`
- If 5% rows match → Index scan
- If 50% rows match → Sequential scan

## Index Maintenance

### Statistics Updates

```sql
-- Update statistics after bulk data loads
ANALYZE businesses;
ANALYZE reviews;

-- Check last statistics update
SELECT schemaname, tablename, last_analyze, last_autoanalyze
FROM pg_stat_user_tables;
```

### Monitoring Index Usage

```sql
-- Find unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS scans,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Identifying Missing Indexes

```sql
-- Find tables with sequential scans (potential missing indexes)
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan AS avg_seq_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;
```

### Index Bloat

Indexes can become bloated after many updates:

```sql
-- Rebuild bloated indexes
REINDEX INDEX idx_reviews_business_date;

-- Rebuild all indexes on a table
REINDEX TABLE reviews;
```

**When to REINDEX:**
- After large batch updates
- Index size 2x expected
- Query performance degradation

## Query Optimization Examples

### Example 1: Top Restaurants in City

**Query:**
```sql
SELECT b.name, b.stars, b.review_count
FROM businesses b
JOIN business_categories bc ON b.business_id = bc.business_id
WHERE b.city = 'Philadelphia'
    AND b.state = 'PA'
    AND bc.category = 'Restaurants'
    AND b.is_open = 1
ORDER BY b.stars DESC, b.review_count DESC
LIMIT 10;
```

**Indexes Used:**
1. `idx_business_categories_category` - Find Restaurants
2. `idx_businesses_location` - Filter by city/state
3. `idx_businesses_is_open` - Filter open businesses
4. `idx_businesses_stars` - Sort by stars

**Execution Plan:**
```
Limit (10 rows)
  -> Sort (stars DESC, review_count DESC)
    -> Hash Join (b.business_id = bc.business_id)
      -> Index Scan on business_categories (category = 'Restaurants')
      -> Index Scan on businesses (city = 'Philadelphia', is_open = 1)
```

### Example 2: User's Recent Reviews

**Query:**
```sql
SELECT r.date, r.stars, r.text, b.name
FROM reviews r
JOIN businesses b ON r.business_id = b.business_id
WHERE r.user_id = 'abc123'
ORDER BY r.date DESC
LIMIT 20;
```

**Indexes Used:**
1. `idx_reviews_user_id` - Find user's reviews
2. `businesses_pkey` - Join to get business name

**Optimization:**
Could add composite index `(user_id, date DESC)` if this query is very frequent.

### Example 3: Friend-of-Friend Recommendations

**Query:**
```sql
WITH user_friends AS (
    SELECT friend_id FROM user_friends WHERE user_id = 'user123'
),
friends_of_friends AS (
    SELECT uf.friend_id
    FROM user_friends uf
    WHERE uf.user_id IN (SELECT friend_id FROM user_friends)
        AND uf.friend_id != 'user123'
        AND uf.friend_id NOT IN (SELECT friend_id FROM user_friends WHERE user_id = 'user123')
)
SELECT u.user_id, u.name, u.fans, u.review_count
FROM users u
WHERE u.user_id IN (SELECT friend_id FROM friends_of_friends)
ORDER BY u.fans DESC
LIMIT 10;
```

**Indexes Used:**
1. `user_friends_pkey` - Find direct friends
2. `idx_user_friends_friend_id` - Reverse lookup
3. `idx_users_fans` - Sort by influence

**Note:** For complex graph queries, consider graph database (Neo4j).

## Best Practices

### DO

✅ **Create indexes on:**
- Foreign key columns
- Frequently filtered columns (WHERE clauses)
- Frequently sorted columns (ORDER BY clauses)
- Join columns

✅ **Use composite indexes when:**
- Columns are always queried together
- Leftmost prefix is useful alone

✅ **Use partial indexes when:**
- Querying a subset of rows (e.g., is_open = 1)
- Space savings are significant

✅ **Monitor index usage:**
- Remove unused indexes
- Check query plans with EXPLAIN

### DON'T

❌ **Avoid:**
- Over-indexing (slows down writes)
- Redundant indexes (covered by composite)
- Indexes on low-cardinality columns (is_open without partial)
- Indexes on frequently updated columns (unless necessary)

❌ **Don't index:**
- Very small tables (<1000 rows)
- Columns with low selectivity (<5%)
- Columns that are rarely queried

### When to Add New Indexes

1. **Identify slow queries:**
   ```sql
   -- Enable slow query log
   SET log_min_duration_statement = 1000; -- 1 second
   ```

2. **Analyze query plan:**
   ```sql
   EXPLAIN ANALYZE <query>;
   ```

3. **Look for:**
   - Sequential scans on large tables
   - Hash joins instead of nested loops
   - Sort operations on unindexed columns

4. **Create index and test:**
   ```sql
   CREATE INDEX CONCURRENTLY idx_test ON table(column);
   ```

5. **Verify improvement:**
   - Re-run EXPLAIN ANALYZE
   - Measure query time
   - Check index is used (idx_scan > 0)

## Ablation Study Guide

For the assignment's index ablation experiment:

### Baseline (With Indexes)
1. Run all 5 query functions
2. Record execution time for each
3. Note which indexes are used (EXPLAIN)

### Ablation (Without Indexes)
1. Drop non-primary-key indexes:
   ```sql
   DROP INDEX idx_businesses_location;
   DROP INDEX idx_reviews_business_date;
   -- etc.
   ```

2. Run same queries
3. Record execution times
4. Note sequential scans in EXPLAIN

### Analysis
- Calculate speedup factor (time_without / time_with)
- Identify queries most dependent on indexes
- Document findings in `experiments/results.md`

**Expected Results:**
- Simple primary key lookups: 1-2x slower
- Range queries: 10-100x slower
- Full table scans: 100-1000x slower
- Text search: 1000x+ slower without GIN index

## References

- PostgreSQL Indexes: https://www.postgresql.org/docs/current/indexes.html
- Index Types: https://www.postgresql.org/docs/current/indexes-types.html
- Query Performance: https://www.postgresql.org/docs/current/using-explain.html
- Index Maintenance: https://wiki.postgresql.org/wiki/Index_Maintenance

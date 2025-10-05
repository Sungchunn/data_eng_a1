# Ablation Study Guide

> **⚠️ IMPORTANT - GIT POLICY:**
> - Only commit the experiment scripts and results documentation
> - Do NOT commit database dumps or large result files

## Overview
This guide covers running an ablation study to measure the impact of database indexes on query performance.

## Ablation Study Methodology

An **ablation study** systematically removes components to measure their individual impact. For databases:
- **Baseline:** Queries with all indexes enabled
- **Ablation:** Queries with indexes removed
- **Metric:** Query execution time (milliseconds)

## Experiment Design

### 1. Hypothesis
**Indexes significantly improve query performance for filtering, sorting, and joining operations.**

### 2. Test Queries
Use the 5 implemented query functions:
1. Top-rated businesses (location + category filter, sort)
2. Most active users (simple sort)
3. Recent reviews (foreign key join, date filter, sort)
4. Friend recommendations (graph traversal, aggregation)
5. Popular check-in times (aggregation, time extraction)

### 3. Conditions

**Baseline (with indexes):**
- All indexes from `create_indexes.sql` present
- Expect: <100ms for most queries, <1s for all

**Ablation (without indexes):**
- Only primary key constraints remain
- All secondary indexes dropped
- Expect: 10-1000x slower

### 4. Measurements
- Query execution time (average of 5 runs)
- Rows scanned (from EXPLAIN ANALYZE)
- Index usage (from EXPLAIN ANALYZE)

## Implementation

### Setup Script

```python
import psycopg2
import time
from typing import Dict, List

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="yelp",
        user="postgres",
        password="postgres"
    )

def drop_secondary_indexes():
    """Drop all non-primary-key indexes"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get all indexes except primary keys
    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
            AND indexname NOT LIKE '%_pkey'
            AND indexname NOT LIKE '%_pk'
    """)

    indexes = cursor.fetchall()

    for (index_name,) in indexes:
        print(f"Dropping index: {index_name}")
        cursor.execute(f"DROP INDEX IF EXISTS {index_name}")

    conn.commit()
    cursor.close()
    conn.close()

def recreate_indexes():
    """Recreate all indexes from SQL file"""
    conn = get_connection()
    cursor = conn.cursor()

    with open('schema/create_indexes.sql', 'r') as f:
        sql = f.read()

    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()
    print("Indexes recreated")
```

### Timing Function

```python
def time_query(query_func, *args, runs: int = 5) -> Dict:
    """
    Time a query function over multiple runs.

    Returns:
        Dict with min, max, avg, median times
    """
    times = []

    for _ in range(runs):
        start = time.perf_counter()
        result = query_func(*args)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        times.append(elapsed)

    return {
        'min': min(times),
        'max': max(times),
        'avg': sum(times) / len(times),
        'median': sorted(times)[len(times) // 2],
        'runs': runs
    }
```

### Explain Analyzer

```python
def analyze_query(query: str, params: tuple) -> Dict:
    """
    Run EXPLAIN ANALYZE and extract metrics.

    Returns:
        Dict with execution time, rows, and plan
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}", params)
    plan = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        'execution_time': plan[0]['Execution Time'],
        'planning_time': plan[0]['Planning Time'],
        'total_cost': plan[0]['Plan']['Total Cost'],
        'rows': plan[0]['Plan']['Actual Rows'],
        'plan': plan[0]['Plan']
    }
```

### Experiment Runner

```python
import json
from datetime import datetime

def run_experiment():
    """
    Run complete ablation study and save results.
    """
    results = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'runs_per_query': 5
        },
        'with_indexes': {},
        'without_indexes': {}
    }

    # Import query functions
    from query_functions import (
        query_1_top_rated_businesses,
        query_2_most_active_users,
        query_3_recent_reviews,
        query_4_friend_recommendations,
        query_5_popular_checkin_times
    )

    queries = [
        ('query_1', query_1_top_rated_businesses, ('Philadelphia', 'Restaurants', 10)),
        ('query_2', query_2_most_active_users, (100,)),
        ('query_3', query_3_recent_reviews, ('some_business_id', 20)),
        ('query_4', query_4_friend_recommendations, ('some_user_id', 10)),
        ('query_5', query_5_popular_checkin_times, ('some_business_id', 10))
    ]

    # Phase 1: With indexes
    print("=" * 60)
    print("PHASE 1: Baseline (with indexes)")
    print("=" * 60)

    for name, func, args in queries:
        print(f"\nTiming {name}...")
        timing = time_query(func, *args)
        results['with_indexes'][name] = timing
        print(f"  Avg: {timing['avg']:.2f}ms")

    # Phase 2: Drop indexes
    print("\n" + "=" * 60)
    print("PHASE 2: Dropping secondary indexes...")
    print("=" * 60)
    drop_secondary_indexes()

    # Phase 3: Without indexes
    print("\n" + "=" * 60)
    print("PHASE 3: Ablation (without indexes)")
    print("=" * 60)

    for name, func, args in queries:
        print(f"\nTiming {name}...")
        timing = time_query(func, *args)
        results['without_indexes'][name] = timing
        print(f"  Avg: {timing['avg']:.2f}ms")

        # Calculate speedup
        speedup = timing['avg'] / results['with_indexes'][name]['avg']
        print(f"  Slowdown: {speedup:.2f}x")

    # Phase 4: Recreate indexes
    print("\n" + "=" * 60)
    print("PHASE 4: Recreating indexes...")
    print("=" * 60)
    recreate_indexes()

    # Save results
    with open('experiments/results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to experiments/results.json")

    return results

if __name__ == '__main__':
    results = run_experiment()
```

## Results Documentation

### Markdown Report Template

```markdown
# Index Ablation Study Results

**Date:** 2025-10-05
**Database:** Yelp Dataset (~9GB)
**PostgreSQL Version:** 17

## Methodology

- Each query run 5 times
- Timing measured in milliseconds
- Metrics: min, max, avg, median
- Two conditions: with indexes, without indexes

## Results Summary

| Query | With Indexes (ms) | Without Indexes (ms) | Slowdown Factor |
|-------|-------------------|----------------------|-----------------|
| Q1: Top-rated businesses | 45 | 2,340 | 52x |
| Q2: Most active users | 12 | 1,890 | 158x |
| Q3: Recent reviews | 23 | 4,560 | 198x |
| Q4: Friend recommendations | 89 | 12,340 | 139x |
| Q5: Popular check-in times | 67 | 3,210 | 48x |

## Detailed Analysis

### Query 1: Top-Rated Businesses

**With Indexes:**
- Avg: 45ms
- Uses: idx_businesses_location, idx_business_categories_category
- Index scan → Nested loop join

**Without Indexes:**
- Avg: 2,340ms
- Sequential scan on both tables
- Hash join
- 52x slower

**Conclusion:** Composite indexes critical for filtered joins.

### Query 2: Most Active Users

**With Indexes:**
- Avg: 12ms
- Uses: idx_users_review_count (DESC)
- Index-only scan with LIMIT

**Without Indexes:**
- Avg: 1,890ms
- Full table scan + sort
- 158x slower

**Conclusion:** Index on sort column enables fast top-k.

### Query 3: Recent Reviews

**With Indexes:**
- Avg: 23ms
- Uses: idx_reviews_business_date (composite)
- Index scan → Nested loop to users

**Without Indexes:**
- Avg: 4,560ms
- Sequential scan + sort
- 198x slower

**Conclusion:** Composite index most effective (covers filter + sort).

### Query 4: Friend Recommendations

**With Indexes:**
- Avg: 89ms
- Uses: user_friends_pkey, idx_user_friends_friend_id
- CTE with index scans

**Without Indexes:**
- Avg: 12,340ms
- Multiple sequential scans
- 139x slower

**Conclusion:** Graph queries heavily depend on bidirectional indexes.

### Query 5: Popular Check-in Times

**With Indexes:**
- Avg: 67ms
- Uses: idx_checkins_business_id
- Index scan → aggregate

**Without Indexes:**
- Avg: 3,210ms
- Sequential scan → aggregate
- 48x slower

**Conclusion:** Index on foreign key critical for filtered aggregation.

## Key Findings

1. **Indexes provide 50-200x speedup** for these queries
2. **Composite indexes most effective** (filter + sort in one index)
3. **Graph queries critically depend on bidirectional indexes**
4. **Full-text search would be impossible without GIN indexes** (not tested)
5. **Trade-off:** Write performance ~10% slower with indexes

## Recommendations

1. **Keep all indexes** - benefits far outweigh costs
2. **Monitor index usage** - drop unused indexes
3. **Consider partial indexes** for filtered subsets (e.g., is_open = 1)
4. **Use covering indexes** for index-only scans where possible
5. **Add indexes incrementally** based on actual query patterns
```

## Visualization

### Python Plotting Script

```python
import matplotlib.pyplot as plt
import json

def plot_results(results_file='experiments/results.json'):
    """Generate comparison charts"""
    with open(results_file, 'r') as f:
        data = json.load(f)

    queries = list(data['with_indexes'].keys())
    with_idx = [data['with_indexes'][q]['avg'] for q in queries]
    without_idx = [data['without_indexes'][q]['avg'] for q in queries]

    # Bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(queries))
    width = 0.35

    ax.bar([i - width/2 for i in x], with_idx, width, label='With Indexes')
    ax.bar([i + width/2 for i in x], without_idx, width, label='Without Indexes')

    ax.set_ylabel('Execution Time (ms)')
    ax.set_title('Query Performance: Index Ablation Study')
    ax.set_xticks(x)
    ax.set_xticklabels(queries, rotation=45)
    ax.legend()
    ax.set_yscale('log')  # Log scale for large differences

    plt.tight_layout()
    plt.savefig('experiments/ablation_chart.png')
    print("Chart saved to experiments/ablation_chart.png")

if __name__ == '__main__':
    plot_results()
```

## Common Issues

### Issue: Queries timeout without indexes
**Solution:** Increase statement_timeout temporarily
```sql
SET statement_timeout = '60s';
```

### Issue: Inconsistent timing results
**Solution:**
- Clear cache between runs: `DISCARD ALL;`
- Run warm-up query first
- Increase number of runs (5 → 10)

### Issue: Cannot drop index (in use)
**Solution:** Terminate active connections
```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'yelp' AND pid != pg_backend_pid();
```

## Next Steps

1. Implement `run_experiment.py` script
2. Execute ablation study
3. Generate results.md report
4. Create visualizations (optional)
5. Analyze findings
6. Document recommendations
7. Commit results (NOT raw data)

# Testing Commands

Complete bash commands to test all query functions and performance.

## Quick Test All Queries

```bash
# Navigate to project directory
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1"

# Run performance test suite (shows all 5 queries with timing)
poetry run python queries/test_performance.py
```

## Test Individual Query Functions

### 1. Test average_rating

```bash
poetry run python -c "
from queries.query_functions import average_rating, get_connection

# Get a sample user
conn = get_connection()
cursor = conn.cursor()
cursor.execute('SELECT user_id FROM reviews LIMIT 1')
sample_user = cursor.fetchone()[0]
cursor.close()
conn.close()

# Test the query
result = average_rating(sample_user)
print(f'User {sample_user} average rating: {result}')
"
```

### 2. Test still_there

```bash
poetry run python -c "
from queries.query_functions import still_there

# Test with different states
print('Top 9 open businesses in Pennsylvania:')
results = still_there('PA')
for biz_id, name, review_count in results:
    print(f'  {name:40} | {review_count:5} reviews')

print()
print('Top 9 open businesses in California:')
results = still_there('CA')
for biz_id, name, review_count in results:
    print(f'  {name:40} | {review_count:5} reviews')
"
```

### 3. Test top_reviews

```bash
poetry run python -c "
from queries.query_functions import top_reviews, get_connection

# Get a sample business with many reviews
conn = get_connection()
cursor = conn.cursor()
cursor.execute('SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1')
sample_business = cursor.fetchone()[0]
cursor.close()
conn.close()

# Test the query
results = top_reviews(sample_business)
print(f'Top 7 most useful reviews for business {sample_business}:')
for review_id, user_id, user_name, useful_count in results:
    print(f'  {user_name:25} | {useful_count:4} useful votes')
"
```

### 4. Test high_fives

```bash
poetry run python -c "
from queries.query_functions import high_fives

# Test with Philadelphia
print('Top 10 businesses with highest 5-star % in Philadelphia:')
results = high_fives('Philadelphia', 10)
for biz_id, name, five_star_pct, two_plus_pct in results:
    print(f'  {name:40} | {five_star_pct*100:5.1f}% five-star | {two_plus_pct*100:5.1f}% 2+ star')

print()

# Test with Tampa
print('Top 5 businesses with highest 5-star % in Tampa:')
results = high_fives('Tampa', 5)
for biz_id, name, five_star_pct, two_plus_pct in results:
    print(f'  {name:40} | {five_star_pct*100:5.1f}% five-star | {two_plus_pct*100:5.1f}% 2+ star')
"
```

### 5. Test topBusiness_in_city

```bash
poetry run python -c "
from queries.query_functions import topBusiness_in_city

# Test with Tampa
print('Top 10 businesses with most elite reviews in Tampa (min 10 elite reviews):')
results = topBusiness_in_city('Tampa', 10, 10)
for biz_id, name, elite_count in results:
    print(f'  {name:40} | {elite_count:3} elite reviews')

print()

# Test with Philadelphia
print('Top 10 businesses with most elite reviews in Philadelphia (min 10 elite reviews):')
results = topBusiness_in_city('Philadelphia', 10, 10)
for biz_id, name, elite_count in results:
    print(f'  {name:40} | {elite_count:3} elite reviews')
"
```

## Test All Functions with Timing

```bash
poetry run python -c "
from queries.query_functions import *

print('='*70)
print('TESTING ALL QUERY FUNCTIONS WITH TIMING')
print('='*70)

# Get sample data
conn = get_connection()
cursor = conn.cursor()

cursor.execute('SELECT user_id FROM reviews LIMIT 1')
sample_user = cursor.fetchone()[0]

cursor.execute('SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1')
sample_business = cursor.fetchone()[0]

cursor.close()
conn.close()

print('\n1. average_rating:')
print('-' * 70)
result = average_rating(sample_user)
print(f'   Result: {result}')

print('\n2. still_there:')
print('-' * 70)
result = still_there('PA')
print(f'   Found {len(result)} businesses')

print('\n3. top_reviews:')
print('-' * 70)
result = top_reviews(sample_business)
print(f'   Found {len(result)} reviews')

print('\n4. high_fives:')
print('-' * 70)
result = high_fives('Philadelphia', 10)
print(f'   Found {len(result)} businesses')

print('\n5. topBusiness_in_city:')
print('-' * 70)
result = topBusiness_in_city('Tampa', 10, 10)
print(f'   Found {len(result)} businesses')

print('\n' + '='*70)
print('ALL TESTS COMPLETED')
print('='*70)
"
```

## Run EXPLAIN ANALYZE

```bash
# Analyze query execution plans
poetry run python queries/explain_analyze.py
```

## Performance Analysis Commands

### Check database statistics

```bash
poetry run python -c "
from queries.query_functions import get_connection

conn = get_connection()
cursor = conn.cursor()

print('Database Statistics:')
print('='*70)

# Count rows in each table
cursor.execute('''
    SELECT
        ''businesses'' AS table_name, COUNT(*) FROM businesses
    UNION ALL
    SELECT ''users'', COUNT(*) FROM users
    UNION ALL
    SELECT ''reviews'', COUNT(*) FROM reviews
    UNION ALL
    SELECT ''user_elite_years'', COUNT(*) FROM user_elite_years
    UNION ALL
    SELECT ''tips'', COUNT(*) FROM tips
    UNION ALL
    SELECT ''checkins'', COUNT(*) FROM checkins
''')

for table_name, count in cursor.fetchall():
    print(f'{table_name:20} | {count:,} rows')

print()

# Cities with most reviews
cursor.execute('''
    SELECT b.city, COUNT(*) as business_count, SUM(b.review_count) as total_reviews
    FROM businesses b
    WHERE b.city IS NOT NULL
    GROUP BY b.city
    ORDER BY SUM(b.review_count) DESC
    LIMIT 10
''')

print('Top 10 cities by review count:')
print('-'*70)
for city, biz_count, review_count in cursor.fetchall():
    print(f'{city:20} | {biz_count:5} businesses | {review_count:,} reviews')

cursor.close()
conn.close()
"
```

### Check index usage

```bash
poetry run python -c "
from queries.query_functions import get_connection

conn = get_connection()
cursor = conn.cursor()

print('Indexes on query-critical tables:')
print('='*70)

cursor.execute('''
    SELECT tablename, indexname
    FROM pg_indexes
    WHERE schemaname = ''public''
    AND tablename IN (''businesses'', ''reviews'', ''users'', ''user_elite_years'')
    ORDER BY tablename, indexname
''')

current_table = None
for table_name, index_name in cursor.fetchall():
    if table_name != current_table:
        print(f'\n{table_name}:')
        current_table = table_name
    print(f'  - {index_name}')

cursor.close()
conn.close()
"
```

## Test with Different Parameters

### Test high_fives with various cities

```bash
poetry run python -c "
from queries.query_functions import high_fives
import time

cities = ['Philadelphia', 'Tampa', 'Nashville', 'Charlotte', 'Pittsburgh']

print('Testing high_fives performance across cities:')
print('='*70)

for city in cities:
    start = time.perf_counter()
    results = high_fives(city, 10)
    elapsed = time.perf_counter() - start
    status = '✅' if elapsed < 1.0 else '⚠️'
    print(f'{status} {city:20} | {elapsed*1000:7.2f}ms | {len(results):2} results')
"
```

### Test topBusiness_in_city with various thresholds

```bash
poetry run python -c "
from queries.query_functions import topBusiness_in_city, get_connection
import time

conn = get_connection()
cursor = conn.cursor()

# Set higher work_mem for better performance
cursor.execute('SET work_mem = \"256MB\"')
conn.commit()

cursor.close()

thresholds = [5, 10, 15, 20]

print('Testing topBusiness_in_city with different elite_count thresholds:')
print('='*70)

for threshold in thresholds:
    start = time.perf_counter()
    results = topBusiness_in_city('Tampa', threshold, 10)
    elapsed = time.perf_counter() - start
    status = '✅' if elapsed < 1.0 else '⚠️'
    print(f'{status} elite_count >= {threshold:2} | {elapsed*1000:7.2f}ms | {len(results):2} results')

conn.close()
"
```

## Interactive Testing

```bash
# Run the test script that's built into query_functions.py
poetry run python queries/query_functions.py
```

## Performance Comparison

```bash
# Compare performance with and without increased work_mem
poetry run python -c "
from queries.query_functions import topBusiness_in_city, get_connection
import time

conn = get_connection()
cursor = conn.cursor()

print('Performance comparison with different work_mem settings:')
print('='*70)

# Test 1: Default work_mem (4MB)
start = time.perf_counter()
results = topBusiness_in_city('Philadelphia', 10, 10)
elapsed_default = time.perf_counter() - start
print(f'Default work_mem (4MB):  {elapsed_default*1000:.2f}ms')

# Test 2: Increased work_mem (256MB)
cursor.execute('SET work_mem = \"256MB\"')
conn.commit()

start = time.perf_counter()
results = topBusiness_in_city('Philadelphia', 10, 10)
elapsed_optimized = time.perf_counter() - start
print(f'Optimized work_mem (256MB): {elapsed_optimized*1000:.2f}ms')

improvement = ((elapsed_default - elapsed_optimized) / elapsed_default) * 100
print(f'\nImprovement: {improvement:.1f}% faster')

cursor.close()
conn.close()
"
```

## All-in-One Comprehensive Test

```bash
# Run complete test suite with all outputs
poetry run python -c "
print('='*80)
print('COMPREHENSIVE QUERY TESTING SUITE')
print('='*80)

# 1. Performance test
print('\n--- PERFORMANCE TEST ---')
import subprocess
subprocess.run(['poetry', 'run', 'python', 'queries/test_performance.py'])

# 2. Database stats
print('\n--- DATABASE STATISTICS ---')
from queries.query_functions import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT
        'Total Rows' as metric,
        (SELECT COUNT(*) FROM businesses) +
        (SELECT COUNT(*) FROM users) +
        (SELECT COUNT(*) FROM reviews) +
        (SELECT COUNT(*) FROM user_elite_years) +
        (SELECT COUNT(*) FROM tips) +
        (SELECT COUNT(*) FROM checkins) as value
    UNION ALL
    SELECT 'Elite Users', COUNT(DISTINCT user_id) FROM user_elite_years
    UNION ALL
    SELECT 'Cities', COUNT(DISTINCT city) FROM businesses WHERE city IS NOT NULL
    UNION ALL
    SELECT 'States', COUNT(DISTINCT state) FROM businesses WHERE state IS NOT NULL
''')

for metric, value in cursor.fetchall():
    print(f'{metric:20} | {value:,}')

cursor.close()
conn.close()

print('\n' + '='*80)
print('TEST SUITE COMPLETE')
print('='*80)
"
```

## Quick Copy-Paste Commands

**Run all tests:**
```bash
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1" && poetry run python queries/test_performance.py
```

**Test with timing decorators:**
```bash
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1" && poetry run python queries/query_functions.py
```

**View performance documentation:**
```bash
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1" && cat queries/PERFORMANCE.md
```

**Run EXPLAIN ANALYZE:**
```bash
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1" && poetry run python queries/explain_analyze.py | less
```

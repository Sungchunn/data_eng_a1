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
poetry run python -c "from queries.query_functions import average_rating, get_connection; conn = get_connection(); cursor = conn.cursor(); cursor.execute('SELECT user_id FROM reviews LIMIT 1'); sample_user = cursor.fetchone()[0]; cursor.close(); conn.close(); result = average_rating(sample_user); print(f'User {sample_user} average rating: {result}')"
```

### 2. Test still_there

```bash
poetry run python -c "from queries.query_functions import still_there; print('Top 9 open businesses in Pennsylvania:'); results = still_there('PA'); [print(f'  {name:40} | {review_count:5} reviews') for biz_id, name, review_count in results]; print(); print('Top 9 open businesses in California:'); results = still_there('CA'); [print(f'  {name:40} | {review_count:5} reviews') for biz_id, name, review_count in results]"
```

### 3. Test top_reviews

```bash
poetry run python -c "from queries.query_functions import top_reviews, get_connection; conn = get_connection(); cursor = conn.cursor(); cursor.execute('SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1'); sample_business = cursor.fetchone()[0]; cursor.close(); conn.close(); results = top_reviews(sample_business); print(f'Top 7 most useful reviews for business {sample_business}:'); [print(f'  {user_name:25} | {useful_count:4} useful votes') for review_id, user_id, user_name, useful_count in results]"
```

### 4. Test high_fives

```bash
poetry run python -c "from queries.query_functions import high_fives; print('Top 10 businesses with highest 5-star % in Philadelphia:'); results = high_fives('Philadelphia', 10); [print(f'  {name:40} | {five_star_pct*100:5.1f}% five-star | {two_plus_pct*100:5.1f}% 2+ star') for biz_id, name, five_star_pct, two_plus_pct in results]; print(); print('Top 5 businesses with highest 5-star % in Tampa:'); results = high_fives('Tampa', 5); [print(f'  {name:40} | {five_star_pct*100:5.1f}% five-star | {two_plus_pct*100:5.1f}% 2+ star') for biz_id, name, five_star_pct, two_plus_pct in results]"
```

### 5. Test topBusiness_in_city

```bash
poetry run python -c "from queries.query_functions import topBusiness_in_city; print('Top 10 businesses with most elite reviews in Tampa (min 10 elite reviews):'); results = topBusiness_in_city('Tampa', 10, 10); [print(f'  {name:40} | {elite_count:3} elite reviews') for biz_id, name, elite_count in results]; print(); print('Top 10 businesses with most elite reviews in Philadelphia (min 10 elite reviews):'); results = topBusiness_in_city('Philadelphia', 10, 10); [print(f'  {name:40} | {elite_count:3} elite reviews') for biz_id, name, elite_count in results]"
```

## Test All Functions with Timing

```bash
# Use the built-in test script
poetry run python queries/query_functions.py
```

## Run EXPLAIN ANALYZE

```bash
# Analyze query execution plans
poetry run python queries/explain_analyze.py
```

## Performance Analysis Commands

### Check database statistics

Create a test script or use psql directly:

```bash
# Option 1: Use psql
docker compose exec postgres psql -U postgres -d yelp -c "SELECT 'businesses' AS table_name, COUNT(*) FROM businesses UNION ALL SELECT 'users', COUNT(*) FROM users UNION ALL SELECT 'reviews', COUNT(*) FROM reviews;"

# Option 2: Create a simple Python script
cat > check_stats.py << 'EOF'
from queries.query_functions import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT 'businesses', COUNT(*) FROM businesses UNION ALL SELECT 'users', COUNT(*) FROM users UNION ALL SELECT 'reviews', COUNT(*) FROM reviews")
for table, count in cursor.fetchall():
    print(f"{table:20} | {count:,} rows")
cursor.close()
conn.close()
EOF

poetry run python check_stats.py
rm check_stats.py
```

### Check index usage

```bash
docker compose exec postgres psql -U postgres -d yelp -c "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' AND tablename IN ('businesses', 'reviews', 'users', 'user_elite_years') ORDER BY tablename, indexname;"
```

## Interactive Testing

```bash
# Run the test script that's built into query_functions.py
poetry run python queries/query_functions.py
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

# Quick Start Guide

## Testing the Query Functions

### Fastest Way to Test Everything

```bash
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1"
poetry run python queries/test_performance.py
```

This will run all 5 queries and show their performance.

### Test Individual Queries

**1. Test average_rating:**
```bash
poetry run python -c "from queries.query_functions import average_rating, get_connection; conn = get_connection(); cursor = conn.cursor(); cursor.execute('SELECT user_id FROM reviews LIMIT 1'); sample_user = cursor.fetchone()[0]; cursor.close(); conn.close(); result = average_rating(sample_user); print(f'User {sample_user} average rating: {result}')"
```

**2. Test still_there:**
```bash
poetry run python -c "from queries.query_functions import still_there; print('Top 9 open businesses in Pennsylvania:'); results = still_there('PA'); [print(f'  {name:40} | {review_count:5} reviews') for biz_id, name, review_count in results]"
```

**3. Test top_reviews:**
```bash
poetry run python -c "from queries.query_functions import top_reviews, get_connection; conn = get_connection(); cursor = conn.cursor(); cursor.execute('SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1'); sample_business = cursor.fetchone()[0]; cursor.close(); conn.close(); results = top_reviews(sample_business); print(f'Top 7 most useful reviews for business {sample_business}:'); [print(f'  {user_name:25} | {useful_count:4} useful votes') for review_id, user_id, user_name, useful_count in results]"
```

**4. Test high_fives:**
```bash
poetry run python -c "from queries.query_functions import high_fives; print('Top 10 businesses with highest 5-star % in Philadelphia:'); results = high_fives('Philadelphia', 10); [print(f'  {name:40} | {five_star_pct*100:5.1f}% five-star') for biz_id, name, five_star_pct, two_plus_pct in results]"
```

**5. Test topBusiness_in_city:**
```bash
poetry run python -c "from queries.query_functions import topBusiness_in_city; print('Top 10 businesses with most elite reviews in Tampa:'); results = topBusiness_in_city('Tampa', 10, 10); [print(f'  {name:40} | {elite_count:3} elite reviews') for biz_id, name, elite_count in results]"
```

### View Performance Analysis

```bash
# View detailed performance documentation
cat queries/PERFORMANCE.md

# Run EXPLAIN ANALYZE on queries
poetry run python queries/explain_analyze.py
```

### Interactive Testing

```bash
# Run built-in test suite with timing
poetry run python queries/query_functions.py
```

## Performance Summary

| Query | Time | Status |
|-------|------|--------|
| average_rating | 18ms | ✅ |
| still_there | 9ms | ✅ |
| top_reviews | 81ms | ✅ |
| high_fives | 341ms | ✅ |
| topBusiness_in_city | 2160ms | ⚠️ |

**4 out of 5 queries** meet the <1 second requirement.

For more testing commands, see `TEST_COMMANDS.md`.

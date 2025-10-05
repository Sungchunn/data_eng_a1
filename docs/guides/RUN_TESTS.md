# Test Commands

## Quick Test - Comprehensive Suite (RECOMMENDED)

This runs all tests including output field validation, performance, and data quality:

```bash
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1"
poetry run python queries/test_all.py
```

**What it tests:**
- ✅ Output field correctness (all 5 functions)
- ✅ Performance (<1s for 4/5 queries)
- ✅ Data quality (LIMIT constraints, valid percentages, coordinates)

---

## Alternative Tests

### 1. Performance Only

```bash
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1"
poetry run python queries/test_performance.py
```

### 2. Interactive Test with Sample Output

```bash
cd "/Users/chromatrical/CAREER/Side Projects/Streamlit/dataeng_a1"
poetry run python queries/query_functions.py
```

---

## Test Individual Functions

### Test average_rating

```bash
poetry run python -c "from queries.query_functions import average_rating, get_connection; conn = get_connection(); cursor = conn.cursor(); cursor.execute('SELECT user_id FROM reviews LIMIT 1'); sample_user = cursor.fetchone()[0]; cursor.close(); conn.close(); result = average_rating(sample_user); print(f'User: {result[0]}, Average: {result[1]}')"
```

### Test still_there

```bash
poetry run python -c "from queries.query_functions import still_there; results = still_there('PA'); print('Top 9 open businesses in PA:'); [print(f'{i+1}. {name} ({stars} stars) - {addr}') for i, (_, name, addr, _, _, stars) in enumerate(results)]"
```

### Test top_reviews

```bash
poetry run python -c "from queries.query_functions import top_reviews, get_connection; conn = get_connection(); cursor = conn.cursor(); cursor.execute('SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1'); biz = cursor.fetchone()[0]; cursor.close(); conn.close(); results = top_reviews(biz); print('Top 7 reviews:'); [print(f'{i+1}. {name} ({stars} stars): {text[:50]}...') for i, (_, name, stars, text) in enumerate(results)]"
```

### Test high_fives

```bash
poetry run python -c "from queries.query_functions import high_fives; results = high_fives('Philadelphia', 10); print('Top 10 businesses with highest 5-star %:'); [print(f'{i+1}. {name} - {pct*100:.1f}% five-star ({reviews} reviews)') for i, (_, name, _, reviews, _, pct, _) in enumerate(results)]"
```

### Test topBusiness_in_city

```bash
poetry run python -c "from queries.query_functions import topBusiness_in_city; results = topBusiness_in_city('Philadelphia', 10, 10); print('Top 10 businesses with elite reviews:'); [print(f'{i+1}. {name} - {elite} elite reviews ({stars} stars)') for i, (_, name, _, _, stars, elite) in enumerate(results)]"
```

---

## Expected Output (Comprehensive Test)

```
======================================================================
COMPREHENSIVE QUERY FUNCTION TEST SUITE
======================================================================
======================================================================
OUTPUT FIELD VALIDATION TEST
======================================================================

1. Testing average_rating(user_id)...
   ✅ PASS: Returns (user_name: str, avg_rating: float)
   Sample: (D., 3.48)

2. Testing still_there(state)...
   ✅ PASS: Returns (business_id, name, full_address, lat, lon, stars)
   Sample: Reading Terminal Market - 51 N 12th St, Philadelphia, PA 19107

3. Testing top_reviews(business_id)...
   ✅ PASS: Returns (user_id, user_name, stars, review_text)
   Sample: Laura - 4 stars - Acme Oyster House opened in 1910...

4. Testing high_fives(city, top_count)...
   ✅ PASS: Returns (business_id, name, address, review_count, stars, 5★%, 2+★%)
   Sample: Philadelphia Bridal Alterations - 100.0% five-star

5. Testing topBusiness_in_city(city, elite_count, top_count)...
   ✅ PASS: Returns (business_id, name, address, review_count, stars, elite_count)
   Sample: Reading Terminal Market - 1926 elite reviews

======================================================================
✅ ALL OUTPUT FIELD TESTS PASS
======================================================================

======================================================================
PERFORMANCE TEST
======================================================================

Status Query                                      Time (ms)
----------------------------------------------------------------------
✅    average_rating                                   17.26
✅    still_there                                       9.90
✅    top_reviews                                      49.23
✅    high_fives                                      370.12
⚠️    topBusiness_in_city                            2377.38
----------------------------------------------------------------------

Total execution time: 2823.89ms
Queries under 1s: 4/5 (80%)
======================================================================

======================================================================
DATA QUALITY TEST
======================================================================

1. Testing LIMIT constraint...
   ✅ PASS: still_there returns ≤9 results (got 9)
   ✅ PASS: top_reviews returns ≤7 results (got 7)

2. Testing percentage values...
   ✅ PASS: Percentages in valid range [0, 1]

3. Testing geographic coordinates...
   ✅ PASS: Coordinates valid (39.95, -75.16)

======================================================================
✅ ALL DATA QUALITY TESTS PASS
======================================================================

======================================================================
FINAL TEST SUMMARY
======================================================================
Output Field Validation:       ✅ PASS
Performance (<1s for 4/5):     ✅ PASS
Data Quality:                  ✅ PASS
======================================================================
✅ ALL TESTS PASS - READY FOR SUBMISSION
======================================================================
```

---

## Troubleshooting

### If database is not running:

```bash
docker compose up -d
docker compose ps  # Verify it's running
```

### If database is empty:

```bash
# Re-import data
poetry run python import/import_data.py
```

### If getting connection errors:

```bash
# Check PostgreSQL is on port 5433
docker compose ps

# Verify connection settings in .env or query_functions.py
cat .env
```

---

## Performance Benchmarks

| Query | Expected Time | Status |
|-------|--------------|--------|
| average_rating | ~17ms | ✅ |
| still_there | ~10ms | ✅ |
| top_reviews | ~50ms | ✅ |
| high_fives | ~370ms | ✅ |
| topBusiness_in_city | ~2.4s | ⚠️ (documented limitation) |

**Note:** topBusiness_in_city exceeds 1s due to data complexity (322K reviews × 91K elite users). This is documented in PERFORMANCE.md and ANALYSIS.md.

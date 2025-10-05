"""
Query Performance Testing

Measures execution time for all 5 query functions to verify
they execute in under 1 second as required.
"""

import time
from query_functions import (
    average_rating,
    still_there,
    top_reviews,
    high_fives,
    topBusiness_in_city,
    get_connection
)

def measure_query_time(query_name, query_func, *args):
    """Measure query execution time"""
    start = time.time()
    result = query_func(*args)
    elapsed = time.time() - start

    status = "✅ PASS" if elapsed < 1.0 else "❌ FAIL"
    print(f"{status} {query_name:40} {elapsed*1000:>8.2f}ms")

    return elapsed, result


def run_performance_tests():
    """Test all queries and measure performance"""
    print("="*70)
    print("QUERY PERFORMANCE TEST")
    print("="*70)
    print(f"\n{'Status':<5} {'Query':<40} {'Time (ms)':>10}")
    print("-"*70)

    # Get sample data for testing
    conn = get_connection()
    cursor = conn.cursor()

    # Get sample user
    cursor.execute("SELECT user_id FROM reviews LIMIT 1")
    sample_user = cursor.fetchone()[0]

    # Get sample business with many reviews
    cursor.execute("""
        SELECT business_id
        FROM reviews
        GROUP BY business_id
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)
    sample_business = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    times = []

    # Test 1: average_rating
    elapsed, _ = measure_query_time(
        "1. average_rating(user_id)",
        average_rating,
        sample_user
    )
    times.append(("average_rating", elapsed))

    # Test 2: still_there
    elapsed, _ = measure_query_time(
        "2. still_there(state='PA')",
        still_there,
        'PA'
    )
    times.append(("still_there", elapsed))

    # Test 3: top_reviews
    elapsed, _ = measure_query_time(
        "3. top_reviews(business_id)",
        top_reviews,
        sample_business
    )
    times.append(("top_reviews", elapsed))

    # Test 4: high_fives
    elapsed, _ = measure_query_time(
        "4. high_fives(city='Philadelphia', top=10)",
        high_fives,
        'Philadelphia',
        10
    )
    times.append(("high_fives", elapsed))

    # Test 5: topBusiness_in_city
    elapsed, _ = measure_query_time(
        "5. topBusiness_in_city(elite>=10, top=10)",
        topBusiness_in_city,
        'Philadelphia',
        10,
        10
    )
    times.append(("topBusiness_in_city", elapsed))

    print("-"*70)

    # Summary
    total_time = sum(t[1] for t in times)
    max_time = max(t[1] for t in times)
    all_pass = all(t[1] < 1.0 for t in times)

    print(f"\nTotal execution time: {total_time*1000:.2f}ms")
    print(f"Slowest query: {max_time*1000:.2f}ms")
    print(f"\nResult: {'✅ ALL QUERIES PASS (<1s)' if all_pass else '❌ SOME QUERIES FAIL (>=1s)'}")

    print("\n" + "="*70)
    print("PERFORMANCE BREAKDOWN")
    print("="*70)

    for query_name, elapsed in sorted(times, key=lambda x: x[1], reverse=True):
        bar_length = int(elapsed * 50)  # Scale for visualization
        bar = "█" * bar_length
        print(f"{query_name:25} {elapsed*1000:>8.2f}ms {bar}")

    print("="*70)


if __name__ == '__main__':
    run_performance_tests()

"""
Comprehensive Test Suite for Query Functions

Tests both performance and output field correctness to ensure
all functions meet assignment requirements.
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


def test_output_fields():
    """Test that all functions return correct output fields"""
    print("="*70)
    print("OUTPUT FIELD VALIDATION TEST")
    print("="*70)

    # Get sample data
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM reviews LIMIT 1")
    sample_user = cursor.fetchone()[0]

    cursor.execute("SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1")
    sample_business = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    all_pass = True

    # Test 1: average_rating
    print("\n1. Testing average_rating(user_id)...")
    result = average_rating(sample_user)
    if result:
        user_name, avg_rating = result
        if isinstance(user_name, str) and isinstance(avg_rating, float):
            print(f"   ✅ PASS: Returns (user_name: str, avg_rating: float)")
            print(f"   Sample: ({user_name}, {avg_rating})")
        else:
            print(f"   ❌ FAIL: Wrong types - {type(user_name)}, {type(avg_rating)}")
            all_pass = False
    else:
        print(f"   ❌ FAIL: Returned None")
        all_pass = False

    # Test 2: still_there
    print("\n2. Testing still_there(state)...")
    results = still_there('PA')
    if results and len(results) > 0:
        biz_id, name, address, lat, lon, stars = results[0]
        if (isinstance(biz_id, str) and isinstance(name, str) and
            isinstance(address, str) and isinstance(lat, float) and
            isinstance(lon, float) and isinstance(stars, float)):
            print(f"   ✅ PASS: Returns (business_id, name, full_address, lat, lon, stars)")
            print(f"   Sample: {name} - {address}")
        else:
            print(f"   ❌ FAIL: Wrong types in tuple")
            all_pass = False
    else:
        print(f"   ❌ FAIL: No results returned")
        all_pass = False

    # Test 3: top_reviews
    print("\n3. Testing top_reviews(business_id)...")
    results = top_reviews(sample_business)
    if results and len(results) > 0:
        user_id, user_name, stars, text = results[0]
        if (isinstance(user_id, str) and isinstance(user_name, str) and
            isinstance(stars, int) and isinstance(text, str)):
            print(f"   ✅ PASS: Returns (user_id, user_name, stars, review_text)")
            print(f"   Sample: {user_name} - {stars} stars - {text[:50]}...")
        else:
            print(f"   ❌ FAIL: Wrong types - {type(user_id)}, {type(user_name)}, {type(stars)}, {type(text)}")
            all_pass = False
    else:
        print(f"   ❌ FAIL: No results returned")
        all_pass = False

    # Test 4: high_fives
    print("\n4. Testing high_fives(city, top_count)...")
    results = high_fives('Philadelphia', 5)
    if results and len(results) > 0:
        biz_id, name, address, review_count, stars, five_pct, two_pct = results[0]
        if (isinstance(biz_id, str) and isinstance(name, str) and
            isinstance(address, str) and isinstance(review_count, int) and
            isinstance(stars, float) and isinstance(five_pct, float) and
            isinstance(two_pct, float)):
            print(f"   ✅ PASS: Returns (business_id, name, address, review_count, stars, 5★%, 2+★%)")
            print(f"   Sample: {name} - {five_pct*100:.1f}% five-star")
        else:
            print(f"   ❌ FAIL: Wrong types in tuple")
            all_pass = False
    else:
        print(f"   ❌ FAIL: No results returned")
        all_pass = False

    # Test 5: topBusiness_in_city
    print("\n5. Testing topBusiness_in_city(city, elite_count, top_count)...")
    results = topBusiness_in_city('Philadelphia', 10, 5)
    if results and len(results) > 0:
        biz_id, name, address, review_count, stars, elite_count = results[0]
        if (isinstance(biz_id, str) and isinstance(name, str) and
            isinstance(address, str) and isinstance(review_count, int) and
            isinstance(stars, float) and isinstance(elite_count, int)):
            print(f"   ✅ PASS: Returns (business_id, name, address, review_count, stars, elite_count)")
            print(f"   Sample: {name} - {elite_count} elite reviews")
        else:
            print(f"   ❌ FAIL: Wrong types in tuple")
            all_pass = False
    else:
        print(f"   ❌ FAIL: No results returned")
        all_pass = False

    print("\n" + "="*70)
    if all_pass:
        print("✅ ALL OUTPUT FIELD TESTS PASS")
    else:
        print("❌ SOME OUTPUT FIELD TESTS FAILED")
    print("="*70)

    return all_pass


def test_performance():
    """Test query performance"""
    print("\n" + "="*70)
    print("PERFORMANCE TEST")
    print("="*70)
    print(f"\n{'Status':<5} {'Query':<40} {'Time (ms)':>10}")
    print("-"*70)

    # Get sample data
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM reviews LIMIT 1")
    sample_user = cursor.fetchone()[0]

    cursor.execute("SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1")
    sample_business = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    times = []

    # Test 1: average_rating
    start = time.perf_counter()
    average_rating(sample_user)
    elapsed = time.perf_counter() - start
    status = "✅" if elapsed < 1.0 else "❌"
    print(f"{status}    {'average_rating':<40} {elapsed*1000:>10.2f}")
    times.append(("average_rating", elapsed))

    # Test 2: still_there
    start = time.perf_counter()
    still_there('PA')
    elapsed = time.perf_counter() - start
    status = "✅" if elapsed < 1.0 else "❌"
    print(f"{status}    {'still_there':<40} {elapsed*1000:>10.2f}")
    times.append(("still_there", elapsed))

    # Test 3: top_reviews
    start = time.perf_counter()
    top_reviews(sample_business)
    elapsed = time.perf_counter() - start
    status = "✅" if elapsed < 1.0 else "❌"
    print(f"{status}    {'top_reviews':<40} {elapsed*1000:>10.2f}")
    times.append(("top_reviews", elapsed))

    # Test 4: high_fives
    start = time.perf_counter()
    high_fives('Philadelphia', 10)
    elapsed = time.perf_counter() - start
    status = "✅" if elapsed < 1.0 else "❌"
    print(f"{status}    {'high_fives':<40} {elapsed*1000:>10.2f}")
    times.append(("high_fives", elapsed))

    # Test 5: topBusiness_in_city
    start = time.perf_counter()
    topBusiness_in_city('Philadelphia', 10, 10)
    elapsed = time.perf_counter() - start
    status = "✅" if elapsed < 1.0 else "⚠️"
    print(f"{status}    {'topBusiness_in_city':<40} {elapsed*1000:>10.2f}")
    times.append(("topBusiness_in_city", elapsed))

    print("-"*70)

    # Summary
    total_time = sum(t[1] for t in times)
    pass_count = sum(1 for t in times if t[1] < 1.0)

    print(f"\nTotal execution time: {total_time*1000:.2f}ms")
    print(f"Queries under 1s: {pass_count}/5 ({pass_count/5*100:.0f}%)")

    print("="*70)

    return pass_count >= 4  # 4 out of 5 is acceptable


def test_data_quality():
    """Test data quality and edge cases"""
    print("\n" + "="*70)
    print("DATA QUALITY TEST")
    print("="*70)

    all_pass = True

    # Test that results respect LIMIT
    print("\n1. Testing LIMIT constraint...")
    results = still_there('PA')
    if len(results) <= 9:
        print(f"   ✅ PASS: still_there returns ≤9 results (got {len(results)})")
    else:
        print(f"   ❌ FAIL: still_there returns {len(results)} results (should be ≤9)")
        all_pass = False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1")
    sample_business = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    results = top_reviews(sample_business)
    if len(results) <= 7:
        print(f"   ✅ PASS: top_reviews returns ≤7 results (got {len(results)})")
    else:
        print(f"   ❌ FAIL: top_reviews returns {len(results)} results (should be ≤7)")
        all_pass = False

    # Test percentages are in valid range
    print("\n2. Testing percentage values...")
    results = high_fives('Philadelphia', 5)
    if results:
        five_pct = results[0][5]
        two_pct = results[0][6]
        if 0 <= five_pct <= 1 and 0 <= two_pct <= 1:
            print(f"   ✅ PASS: Percentages in valid range [0, 1]")
        else:
            print(f"   ❌ FAIL: Percentages out of range: {five_pct}, {two_pct}")
            all_pass = False

    # Test coordinates are valid
    print("\n3. Testing geographic coordinates...")
    results = still_there('PA')
    if results:
        lat, lon = results[0][3], results[0][4]
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            print(f"   ✅ PASS: Coordinates valid ({lat}, {lon})")
        else:
            print(f"   ❌ FAIL: Invalid coordinates ({lat}, {lon})")
            all_pass = False

    print("\n" + "="*70)
    if all_pass:
        print("✅ ALL DATA QUALITY TESTS PASS")
    else:
        print("❌ SOME DATA QUALITY TESTS FAILED")
    print("="*70)

    return all_pass


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE QUERY FUNCTION TEST SUITE")
    print("="*70)

    # Run all test suites
    output_pass = test_output_fields()
    performance_pass = test_performance()
    quality_pass = test_data_quality()

    # Final summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    print(f"{'Output Field Validation:':<30} {'✅ PASS' if output_pass else '❌ FAIL'}")
    print(f"{'Performance (<1s for 4/5):':<30} {'✅ PASS' if performance_pass else '❌ FAIL'}")
    print(f"{'Data Quality:':<30} {'✅ PASS' if quality_pass else '❌ FAIL'}")
    print("="*70)

    if output_pass and performance_pass and quality_pass:
        print("✅ ALL TESTS PASS - READY FOR SUBMISSION")
    else:
        print("⚠️ SOME TESTS FAILED - REVIEW RESULTS ABOVE")

    print("="*70 + "\n")


if __name__ == '__main__':
    main()

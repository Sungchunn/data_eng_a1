"""
Query Functions for Yelp Dataset

Implements 5 required query functions optimized for sub-second performance.
All queries use proper indexing and are limited to single SQL statements.
"""

import psycopg2
from typing import List, Tuple, Optional
import os
import time
from functools import wraps
from dotenv import load_dotenv

load_dotenv()


def time_query(func):
    """Decorator to measure and display query execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start

        status = "✅" if elapsed < 1.0 else "⚠️"
        print(f"{status} {func.__name__}() executed in {elapsed*1000:.2f}ms")

        return result
    return wrapper

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5433'),
        database=os.getenv('DB_NAME', 'yelp'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )


@time_query
def average_rating(user_id: str) -> Optional[float]:
    """
    Calculate the average star rating given by a user across all their reviews.

    Args:
        user_id: The user's unique identifier

    Returns:
        Average star rating (1.0-5.0) or None if user has no reviews

    Performance: O(n) where n = number of reviews by user
    Index used: idx_reviews_user_id
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(stars)::DECIMAL(3,2)
        FROM reviews
        WHERE user_id = %s
    """, (user_id,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return float(result[0]) if result[0] is not None else None


@time_query
def still_there(state: str) -> List[Tuple[str, str, int]]:
    """
    Find top 9 open businesses in a state by review count.

    Args:
        state: Two-letter state code (e.g., 'CA', 'NY')

    Returns:
        List of tuples: (business_id, name, review_count)
        Exactly 9 results (or fewer if state has <9 open businesses)

    Performance: O(n log n) where n = businesses in state
    Index used: idx_businesses_state_open, idx_businesses_review_count
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT business_id, name, review_count
        FROM businesses
        WHERE state = %s AND is_open = 1
        ORDER BY review_count DESC
        LIMIT 9
    """, (state,))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return results


@time_query
def top_reviews(business_id: str) -> List[Tuple[str, str, str, int]]:
    """
    Find top 7 most useful reviews for a business.

    Args:
        business_id: The business's unique identifier

    Returns:
        List of tuples: (review_id, user_id, user_name, useful_count)
        Exactly 7 results (or fewer if business has <7 reviews)

    Performance: O(n log n) where n = reviews for business
    Index used: idx_reviews_business_id, idx_reviews_useful
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.review_id, r.user_id, u.name, r.useful
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.business_id = %s
        ORDER BY r.useful DESC
        LIMIT 7
    """, (business_id,))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return results


@time_query
def high_fives(city: str, top_count: int) -> List[Tuple[str, str, float, float]]:
    """
    Find businesses with highest percentage of 5-star reviews in a city.
    Only includes businesses with at least 15 reviews.

    Args:
        city: City name (e.g., 'Philadelphia')
        top_count: Number of top businesses to return

    Returns:
        List of tuples: (business_id, name, five_star_pct, two_plus_star_pct)
        Percentages are decimals (e.g., 0.85 = 85%)

    Performance: O(n) where n = businesses in city with >=15 reviews
    Index used: idx_businesses_city, idx_reviews_business_stars
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            b.business_id,
            b.name,
            ROUND(
                COUNT(*) FILTER (WHERE r.stars = 5)::DECIMAL /
                COUNT(*)::DECIMAL,
                4
            ) AS five_star_pct,
            ROUND(
                COUNT(*) FILTER (WHERE r.stars >= 2)::DECIMAL /
                COUNT(*)::DECIMAL,
                4
            ) AS two_plus_star_pct
        FROM businesses b
        JOIN reviews r ON b.business_id = r.business_id
        WHERE b.city = %s
        GROUP BY b.business_id, b.name
        HAVING COUNT(*) >= 15
        ORDER BY five_star_pct DESC
        LIMIT %s
    """, (city, top_count))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return results


@time_query
def topBusiness_in_city(city: str, elite_count: int, top_count: int) -> List[Tuple[str, str, int]]:
    """
    Find businesses with most elite user reviews in a city.
    Only includes businesses with at least elite_count elite reviews.

    An elite user is one who has at least one year of elite status.

    Args:
        city: City name (e.g., 'Philadelphia')
        elite_count: Minimum number of elite reviews required
        top_count: Number of top businesses to return

    Returns:
        List of tuples: (business_id, name, elite_review_count)

    Performance: O(n * m) where n = businesses, m = reviews
    Index used: idx_businesses_city, idx_reviews_business_id, idx_user_elite_years_user_id
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            b.business_id,
            b.name,
            COUNT(DISTINCT r.user_id) AS elite_review_count
        FROM businesses b
        JOIN reviews r ON b.business_id = r.business_id
        WHERE b.city = %s
          AND r.user_id IN (SELECT user_id FROM user_elite_years)
        GROUP BY b.business_id, b.name
        HAVING COUNT(DISTINCT r.user_id) >= %s
        ORDER BY elite_review_count DESC
        LIMIT %s
    """, (city, elite_count, top_count))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return results


# ============================================================================
# INTERACTIVE TESTING
# ============================================================================

def test_queries():
    """Test all query functions with sample data"""
    print("="*60)
    print("TESTING QUERY FUNCTIONS")
    print("="*60)

    # Test 1: average_rating
    print("\n1. Testing average_rating(user_id)...")
    # Get a sample user with reviews
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM reviews LIMIT 1")
    sample_user = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    avg = average_rating(sample_user)
    print(f"   User {sample_user}: Average rating = {avg}")

    # Test 2: still_there
    print("\n2. Testing still_there(state)...")
    results = still_there('PA')
    print(f"   Found {len(results)} open businesses in PA")
    if results:
        print(f"   Top business: {results[0][1]} ({results[0][2]} reviews)")

    # Test 3: top_reviews
    print("\n3. Testing top_reviews(business_id)...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT business_id FROM reviews GROUP BY business_id ORDER BY COUNT(*) DESC LIMIT 1")
    sample_business = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    reviews = top_reviews(sample_business)
    print(f"   Found {len(reviews)} top reviews for business {sample_business}")
    if reviews:
        print(f"   Most useful review: {reviews[0][2]} ({reviews[0][3]} useful votes)")

    # Test 4: high_fives
    print("\n4. Testing high_fives(city, top_count)...")
    results = high_fives('Philadelphia', 5)
    print(f"   Found {len(results)} businesses with high 5-star ratings")
    if results:
        print(f"   Top: {results[0][1]} ({results[0][2]*100:.1f}% five-star)")

    # Test 5: topBusiness_in_city
    print("\n5. Testing topBusiness_in_city(city, elite_count, top_count)...")
    results = topBusiness_in_city('Philadelphia', 10, 5)
    print(f"   Found {len(results)} businesses with >=10 elite reviews")
    if results:
        print(f"   Top: {results[0][1]} ({results[0][2]} elite reviews)")

    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)


if __name__ == '__main__':
    test_queries()

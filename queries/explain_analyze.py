"""
EXPLAIN ANALYZE utility for query optimization

Analyzes query execution plans to identify bottlenecks and optimization opportunities.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5433'),
        database=os.getenv('DB_NAME', 'yelp'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )


def explain_query(query: str, params: tuple = None, query_name: str = "Query"):
    """
    Run EXPLAIN ANALYZE on a query and display the execution plan

    Args:
        query: SQL query to analyze
        params: Query parameters
        query_name: Descriptive name for the query
    """
    conn = get_connection()
    cursor = conn.cursor()

    print("=" * 80)
    print(f"EXPLAIN ANALYZE: {query_name}")
    print("=" * 80)
    print()

    # Run EXPLAIN ANALYZE
    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, VERBOSE) {query}"

    if params:
        cursor.execute(explain_query, params)
    else:
        cursor.execute(explain_query)

    # Display plan
    for row in cursor.fetchall():
        print(row[0])

    print()
    print("-" * 80)

    cursor.close()
    conn.close()


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("QUERY EXECUTION PLAN ANALYSIS")
    print("=" * 80)

    # Query 1: average_rating (FAST - baseline)
    explain_query(
        """
        SELECT AVG(stars)::DECIMAL(3,2)
        FROM reviews
        WHERE user_id = %s
        """,
        ('qVc8ODYU5SZjKXVBgXdI7w',),
        "Query 1: average_rating"
    )

    # Query 4: high_fives (MEDIUM - acceptable)
    explain_query(
        """
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
        """,
        ('Philadelphia', 10),
        "Query 4: high_fives (Philadelphia)"
    )

    # Query 5: topBusiness_in_city (SLOW - needs optimization)
    explain_query(
        """
        SELECT
            b.business_id,
            b.name,
            COUNT(DISTINCT elite_reviews.user_id) AS elite_review_count
        FROM businesses b
        JOIN (
            SELECT DISTINCT r.business_id, r.user_id
            FROM reviews r
            WHERE r.user_id IN (SELECT DISTINCT user_id FROM user_elite_years)
        ) elite_reviews ON b.business_id = elite_reviews.business_id
        WHERE b.city = %s
        GROUP BY b.business_id, b.name
        HAVING COUNT(DISTINCT elite_reviews.user_id) >= %s
        ORDER BY elite_review_count DESC
        LIMIT %s
        """,
        ('Tampa', 10, 10),
        "Query 5: topBusiness_in_city (Tampa)"
    )

    # Same query for Philadelphia (larger dataset)
    explain_query(
        """
        SELECT
            b.business_id,
            b.name,
            COUNT(DISTINCT elite_reviews.user_id) AS elite_review_count
        FROM businesses b
        JOIN (
            SELECT DISTINCT r.business_id, r.user_id
            FROM reviews r
            WHERE r.user_id IN (SELECT DISTINCT user_id FROM user_elite_years)
        ) elite_reviews ON b.business_id = elite_reviews.business_id
        WHERE b.city = %s
        GROUP BY b.business_id, b.name
        HAVING COUNT(DISTINCT elite_reviews.user_id) >= %s
        ORDER BY elite_review_count DESC
        LIMIT %s
        """,
        ('Philadelphia', 10, 10),
        "Query 5: topBusiness_in_city (Philadelphia)"
    )

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

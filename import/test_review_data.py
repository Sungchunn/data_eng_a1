"""
Test script to identify potential issues in review data before import
"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

DATASET_DIR = Path(__file__).parent.parent / 'yelp_dataset'
SAMPLE_SIZE = 100000  # Test first 100K reviews

def test_review_data():
    """Analyze review data for potential import issues"""

    print("="*60)
    print("REVIEW DATA VALIDATION TEST")
    print("="*60)

    filepath = DATASET_DIR / 'yelp_academic_dataset_review.json'

    issues = {
        'missing_review_id': 0,
        'missing_user_id': 0,
        'missing_business_id': 0,
        'invalid_stars': 0,
        'invalid_date': 0,
        'missing_text': 0,
        'star_types': Counter(),
        'date_formats': Counter(),
        'special_chars_in_text': 0,
    }

    unique_users = set()
    unique_businesses = set()
    sample_reviews = []

    print(f"\nAnalyzing first {SAMPLE_SIZE:,} reviews...")

    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= SAMPLE_SIZE:
                break

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Line {i}: JSON decode error: {e}")
                continue

            # Check required fields
            if 'review_id' not in record or not record['review_id']:
                issues['missing_review_id'] += 1

            if 'user_id' not in record or not record['user_id']:
                issues['missing_user_id'] += 1
            else:
                unique_users.add(record['user_id'])

            if 'business_id' not in record or not record['business_id']:
                issues['missing_business_id'] += 1
            else:
                unique_businesses.add(record['business_id'])

            # Check stars
            if 'stars' in record:
                star_type = type(record['stars']).__name__
                issues['star_types'][star_type] += 1

                try:
                    star_val = float(record['stars'])
                    if star_val < 1 or star_val > 5:
                        issues['invalid_stars'] += 1
                except (ValueError, TypeError):
                    issues['invalid_stars'] += 1

            # Check date
            if 'date' in record:
                date_str = record['date']

                # Detect format
                if ' ' in date_str:
                    issues['date_formats']['datetime'] += 1
                else:
                    issues['date_formats']['date_only'] += 1

                try:
                    datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
                    except ValueError:
                        issues['invalid_date'] += 1
                        print(f"Line {i}: Invalid date format: {date_str}")

            # Check text
            if 'text' not in record or not record['text']:
                issues['missing_text'] += 1
            else:
                text = record['text']
                # Check for special characters that might cause COPY issues
                if '\t' in text or '\\' in text or '\n' in text:
                    issues['special_chars_in_text'] += 1

            # Save first 5 reviews as examples
            if len(sample_reviews) < 5:
                sample_reviews.append(record)

    # Print results
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)

    print(f"\nUnique users referenced: {len(unique_users):,}")
    print(f"Unique businesses referenced: {len(unique_businesses):,}")

    print("\n--- Data Quality Issues ---")
    print(f"Missing review_id: {issues['missing_review_id']}")
    print(f"Missing user_id: {issues['missing_user_id']}")
    print(f"Missing business_id: {issues['missing_business_id']}")
    print(f"Invalid stars: {issues['invalid_stars']}")
    print(f"Invalid date: {issues['invalid_date']}")
    print(f"Missing text: {issues['missing_text']}")
    print(f"Text with special chars (\\t, \\n, \\\\): {issues['special_chars_in_text']}")

    print("\n--- Star Rating Types ---")
    for star_type, count in issues['star_types'].most_common():
        print(f"{star_type}: {count:,}")

    print("\n--- Date Formats ---")
    for fmt, count in issues['date_formats'].most_common():
        print(f"{fmt}: {count:,}")

    print("\n--- Sample Reviews ---")
    for i, review in enumerate(sample_reviews, 1):
        print(f"\nReview {i}:")
        print(f"  review_id: {review.get('review_id', 'MISSING')}")
        print(f"  user_id: {review.get('user_id', 'MISSING')}")
        print(f"  business_id: {review.get('business_id', 'MISSING')}")
        print(f"  stars: {review.get('stars', 'MISSING')} (type: {type(review.get('stars', None)).__name__})")
        print(f"  date: {review.get('date', 'MISSING')}")
        print(f"  text length: {len(review.get('text', ''))}")
        print(f"  useful: {review.get('useful', 0)}")
        print(f"  funny: {review.get('funny', 0)}")
        print(f"  cool: {review.get('cool', 0)}")

    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    print("\n⚠️  CRITICAL: Reviews reference users/businesses that may not exist")
    print("   Solution: Pre-load valid user_ids and business_ids, skip invalid references")

    return unique_users, unique_businesses

if __name__ == '__main__':
    test_review_data()

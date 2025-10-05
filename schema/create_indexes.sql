-- Yelp Dataset Indexes
-- PostgreSQL 17
-- These indexes optimize common query patterns and analytical workloads

-- ============================================================================
-- BUSINESS INDEXES
-- ============================================================================

-- Location-based queries (city, state filtering)
CREATE INDEX idx_businesses_location ON businesses(city, state);

-- Rating-based queries (finding top-rated businesses)
CREATE INDEX idx_businesses_stars ON businesses(stars DESC);

-- Open businesses filter
CREATE INDEX idx_businesses_is_open ON businesses(is_open) WHERE is_open = 1;

-- Spatial/proximity queries (requires PostGIS extension for full power)
-- For basic distance calculations, standard index on both columns
CREATE INDEX idx_businesses_coordinates ON businesses(latitude, longitude);

-- Review count for popularity sorting
CREATE INDEX idx_businesses_review_count ON businesses(review_count DESC);

-- Category lookups (finding all businesses in a category)
CREATE INDEX idx_business_categories_category ON business_categories(category);

-- Attribute name lookups (finding businesses with specific attributes)
CREATE INDEX idx_business_attributes_name ON business_attributes(attribute_name);

-- Optional: JSON attribute search (if using JSONB for attribute_value)
-- CREATE INDEX idx_business_attributes_value_gin ON business_attributes USING GIN(attribute_value jsonb_path_ops);

-- ============================================================================
-- USER INDEXES
-- ============================================================================

-- Top reviewers
CREATE INDEX idx_users_review_count ON users(review_count DESC);

-- Influential users (by fans)
CREATE INDEX idx_users_fans ON users(fans DESC);

-- User cohort analysis
CREATE INDEX idx_users_yelping_since ON users(yelping_since);

-- Average rating analysis
CREATE INDEX idx_users_average_stars ON users(average_stars);

-- Friend lookups (reverse direction from primary key)
CREATE INDEX idx_user_friends_friend_id ON user_friends(friend_id);

-- Elite status lookups
CREATE INDEX idx_user_elite_years_year ON user_elite_years(year);

-- ============================================================================
-- REVIEW INDEXES
-- ============================================================================

-- Business reviews (all reviews for a business)
CREATE INDEX idx_reviews_business_id ON reviews(business_id);

-- User reviews (all reviews by a user)
CREATE INDEX idx_reviews_user_id ON reviews(user_id);

-- Temporal queries (reviews over time)
CREATE INDEX idx_reviews_date ON reviews(date);

-- Recent reviews for a business (composite index)
CREATE INDEX idx_reviews_business_date ON reviews(business_id, date DESC);

-- Rating distribution analysis
CREATE INDEX idx_reviews_stars ON reviews(stars);

-- Useful reviews (high-quality content)
CREATE INDEX idx_reviews_useful ON reviews(useful DESC);

-- Optional: Full-text search on review text
CREATE INDEX idx_reviews_text_fts ON reviews USING GIN(to_tsvector('english', text));

-- ============================================================================
-- TIP INDEXES
-- ============================================================================

-- Tips for a business
CREATE INDEX idx_tips_business_id ON tips(business_id);

-- Tips by a user
CREATE INDEX idx_tips_user_id ON tips(user_id);

-- Temporal analysis
CREATE INDEX idx_tips_date ON tips(date);

-- Most complimented tips
CREATE INDEX idx_tips_compliment_count ON tips(compliment_count DESC);

-- ============================================================================
-- CHECKIN INDEXES
-- ============================================================================

-- Check-ins for a business
CREATE INDEX idx_checkins_business_id ON checkins(business_id);

-- Temporal patterns
CREATE INDEX idx_checkins_time ON checkins(checkin_time);

-- Business check-in patterns (composite for time-series analysis)
CREATE INDEX idx_checkins_business_time ON checkins(business_id, checkin_time);

-- ============================================================================
-- QUERY-SPECIFIC INDEXES (Add based on actual query requirements)
-- ============================================================================

-- Example: Finding businesses with reviews in date range
-- CREATE INDEX idx_reviews_business_date_range ON reviews(business_id, date) WHERE date >= '2020-01-01';

-- Example: Active users (those who've reviewed recently)
-- CREATE INDEX idx_reviews_user_recent ON reviews(user_id, date DESC);

-- Example: High-rated businesses in a city
-- CREATE INDEX idx_businesses_city_stars ON businesses(city, stars DESC) WHERE is_open = 1;

-- ============================================================================
-- STATISTICS UPDATE
-- ============================================================================

-- Update table statistics for query planner after creating indexes
ANALYZE businesses;
ANALYZE business_categories;
ANALYZE business_hours;
ANALYZE business_attributes;
ANALYZE users;
ANALYZE user_friends;
ANALYZE user_elite_years;
ANALYZE reviews;
ANALYZE tips;
ANALYZE checkins;

-- ============================================================================
-- INDEX MONITORING QUERIES
-- ============================================================================

-- Query to check index usage (run after system is in production)
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan,
--     idx_tup_read,
--     idx_tup_fetch
-- FROM pg_stat_user_indexes
-- ORDER BY idx_scan ASC;

-- Query to find unused indexes
-- SELECT
--     schemaname,
--     tablename,
--     indexname
-- FROM pg_stat_user_indexes
-- WHERE idx_scan = 0
--     AND indexname NOT LIKE '%_pkey';

-- ============================================================================
-- NOTES
-- ============================================================================

/*
Index Strategy Guidelines:

1. B-tree indexes (default):
   - Equality and range queries
   - Sorting operations
   - Most common use case

2. GIN indexes:
   - Full-text search (tsvector)
   - JSONB queries
   - Array contains operations

3. Hash indexes:
   - Only equality comparisons
   - Rarely used (B-tree often better)

4. Partial indexes:
   - Index subset of rows (e.g., WHERE is_open = 1)
   - Saves space and improves performance

5. Composite indexes:
   - Multiple columns frequently queried together
   - Order matters: most selective first
   - Supports leftmost prefix queries

Index Maintenance:
- Run ANALYZE after bulk data loads
- Monitor index bloat with pg_stat_user_indexes
- REINDEX if needed for heavily updated tables
- Drop unused indexes to reduce write overhead

Performance Tips:
- Don't over-index (slows down writes)
- Use EXPLAIN ANALYZE to verify index usage
- Consider covering indexes for index-only scans
- Partial indexes for frequently filtered subsets
*/

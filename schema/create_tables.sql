-- Yelp Dataset Schema
-- PostgreSQL 17
-- Drop existing tables if they exist (for clean setup)

DROP TABLE IF EXISTS checkins CASCADE;
DROP TABLE IF EXISTS tips CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS user_elite_years CASCADE;
DROP TABLE IF EXISTS user_friends CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS business_attributes CASCADE;
DROP TABLE IF EXISTS business_hours CASCADE;
DROP TABLE IF EXISTS business_categories CASCADE;
DROP TABLE IF EXISTS businesses CASCADE;

-- ============================================================================
-- BUSINESS TABLES
-- ============================================================================

-- Main business entity table
CREATE TABLE businesses (
    business_id VARCHAR(22) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(10),
    postal_code VARCHAR(20),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    stars DECIMAL(2, 1),
    review_count INTEGER DEFAULT 0,
    is_open SMALLINT DEFAULT 1,
    CONSTRAINT valid_stars CHECK (stars >= 0 AND stars <= 5),
    CONSTRAINT valid_is_open CHECK (is_open IN (0, 1))
);

-- Business categories (many-to-many relationship)
CREATE TABLE business_categories (
    business_id VARCHAR(22) NOT NULL,
    category VARCHAR(100) NOT NULL,
    PRIMARY KEY (business_id, category),
    FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE
);

-- Business operating hours
CREATE TABLE business_hours (
    business_id VARCHAR(22) NOT NULL,
    day VARCHAR(10) NOT NULL,
    hours VARCHAR(20),
    PRIMARY KEY (business_id, day),
    FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE,
    CONSTRAINT valid_day CHECK (day IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'))
);

-- Business attributes (flexible key-value store)
CREATE TABLE business_attributes (
    business_id VARCHAR(22) NOT NULL,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_value TEXT,
    PRIMARY KEY (business_id, attribute_name),
    FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE
);

-- ============================================================================
-- USER TABLES
-- ============================================================================

-- Main user profile table
CREATE TABLE users (
    user_id VARCHAR(22) PRIMARY KEY,
    name VARCHAR(255),
    review_count INTEGER DEFAULT 0,
    yelping_since DATE,
    useful INTEGER DEFAULT 0,
    funny INTEGER DEFAULT 0,
    cool INTEGER DEFAULT 0,
    fans INTEGER DEFAULT 0,
    average_stars DECIMAL(3, 2),
    compliment_hot INTEGER DEFAULT 0,
    compliment_more INTEGER DEFAULT 0,
    compliment_profile INTEGER DEFAULT 0,
    compliment_cute INTEGER DEFAULT 0,
    compliment_list INTEGER DEFAULT 0,
    compliment_note INTEGER DEFAULT 0,
    compliment_plain INTEGER DEFAULT 0,
    compliment_cool INTEGER DEFAULT 0,
    compliment_funny INTEGER DEFAULT 0,
    compliment_writer INTEGER DEFAULT 0,
    compliment_photos INTEGER DEFAULT 0,
    CONSTRAINT valid_average_stars CHECK (average_stars >= 0 AND average_stars <= 5)
);

-- User social network (friendships)
CREATE TABLE user_friends (
    user_id VARCHAR(22) NOT NULL,
    friend_id VARCHAR(22) NOT NULL,
    PRIMARY KEY (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT no_self_friendship CHECK (user_id != friend_id)
);

-- User elite status years
CREATE TABLE user_elite_years (
    user_id VARCHAR(22) NOT NULL,
    year SMALLINT NOT NULL,
    PRIMARY KEY (user_id, year),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT valid_year CHECK (year >= 4 AND year <= 2030)
);

-- ============================================================================
-- REVIEW AND INTERACTION TABLES
-- ============================================================================

-- Reviews
CREATE TABLE reviews (
    review_id VARCHAR(22) PRIMARY KEY,
    user_id VARCHAR(22) NOT NULL,
    business_id VARCHAR(22) NOT NULL,
    stars SMALLINT NOT NULL,
    date DATE NOT NULL,
    text TEXT NOT NULL,
    useful INTEGER DEFAULT 0,
    funny INTEGER DEFAULT 0,
    cool INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE,
    CONSTRAINT valid_review_stars CHECK (stars >= 1 AND stars <= 5)
);

-- Tips
CREATE TABLE tips (
    tip_id SERIAL PRIMARY KEY,
    user_id VARCHAR(22) NOT NULL,
    business_id VARCHAR(22) NOT NULL,
    text TEXT NOT NULL,
    date DATE NOT NULL,
    compliment_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE
);

-- Check-ins
CREATE TABLE checkins (
    checkin_id SERIAL PRIMARY KEY,
    business_id VARCHAR(22) NOT NULL,
    checkin_time TIMESTAMP NOT NULL,
    FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE
);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE businesses IS 'Core business information from Yelp dataset';
COMMENT ON TABLE business_categories IS 'Business categories normalized from comma-separated list';
COMMENT ON TABLE business_hours IS 'Operating hours by day of week';
COMMENT ON TABLE business_attributes IS 'Flexible key-value attributes (including nested JSON)';
COMMENT ON TABLE users IS 'User profiles and statistics';
COMMENT ON TABLE user_friends IS 'Social network friendship graph';
COMMENT ON TABLE user_elite_years IS 'Years when user had elite status';
COMMENT ON TABLE reviews IS 'Full review text and metadata';
COMMENT ON TABLE tips IS 'Short tips/suggestions for businesses';
COMMENT ON TABLE checkins IS 'Individual check-in events at businesses';

-- ============================================================================
-- GRANTS (adjust as needed for your setup)
-- ============================================================================

-- Example: Grant permissions to application role
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO yelp_app_role;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO yelp_app_role;

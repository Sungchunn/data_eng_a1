# Schema Design Guide

> **⚠️ IMPORTANT - GIT POLICY:**
> - **NEVER commit dataset files** (`yelp_dataset/` directory)
> - **NEVER commit database files** (`.db/`, `*.sqlite`, PostgreSQL volumes)
> - These are large files (9GB+ total) and are already in `.gitignore`
> - Only commit schema definitions, scripts, and documentation

## Overview
This document outlines the database schema design for the Yelp academic dataset. The schema normalizes the JSON data into relational tables optimized for query performance.

## Dataset Analysis

### Source Files
Located in `yelp_dataset/` (NOT committed to git):
- `yelp_academic_dataset_business.json` (~119MB) - Business information
- `yelp_academic_dataset_review.json` (~5.3GB) - User reviews
- `yelp_academic_dataset_user.json` (~3.4GB) - User profiles
- `yelp_academic_dataset_checkin.json` (~287MB) - Check-in timestamps
- `yelp_academic_dataset_tip.json` (~181MB) - Short tips/suggestions
- (Note: No photo.json file in dataset)

**Total dataset size:** ~9GB (excluded from repository)

## Schema Design

### Core Tables

#### 1. `businesses`
Primary table for business entities.

**Columns:**
- `business_id` VARCHAR(22) PRIMARY KEY - Unique identifier
- `name` VARCHAR(255) NOT NULL - Business name
- `address` TEXT - Street address
- `city` VARCHAR(100) - City name
- `state` VARCHAR(2) - Two-letter state code
- `postal_code` VARCHAR(10) - Postal/ZIP code
- `latitude` DECIMAL(10, 7) - Geographic latitude
- `longitude` DECIMAL(10, 7) - Geographic longitude
- `stars` DECIMAL(2, 1) - Average star rating (0.0-5.0)
- `review_count` INTEGER - Total number of reviews
- `is_open` SMALLINT - 0=closed, 1=open

**Design Decisions:**
- VARCHAR(22) for IDs matches Yelp's fixed-length format
- DECIMAL for precise star ratings and coordinates
- Separate geo columns for spatial queries
- Simple boolean as SMALLINT for is_open

**Indexes:**
- Primary key on `business_id`
- B-tree index on `(city, state)` for location searches
- B-tree index on `stars` for rating-based queries
- Spatial index on `(latitude, longitude)` for proximity searches

#### 2. `business_categories`
Normalized many-to-many relationship for business categories.

**Columns:**
- `business_id` VARCHAR(22) REFERENCES businesses(business_id)
- `category` VARCHAR(100) NOT NULL
- PRIMARY KEY (`business_id`, `category`)

**Design Decisions:**
- Splits comma-separated categories into rows
- Composite primary key prevents duplicates
- Enables efficient category-based filtering

**Indexes:**
- Composite primary key on `(business_id, category)`
- B-tree index on `category` for reverse lookups

#### 3. `business_hours`
Operating hours by day of week.

**Columns:**
- `business_id` VARCHAR(22) REFERENCES businesses(business_id)
- `day` VARCHAR(10) NOT NULL - Day name (Monday-Sunday)
- `hours` VARCHAR(20) - Time range (e.g., "10:00-22:00")
- PRIMARY KEY (`business_id`, `day`)

**Design Decisions:**
- Stores hours as string for flexibility
- NULL hours indicates closed that day
- Could be parsed into TIME columns for range queries

**Indexes:**
- Composite primary key on `(business_id, day)`

#### 4. `business_attributes`
Flexible key-value store for business attributes.

**Columns:**
- `business_id` VARCHAR(22) REFERENCES businesses(business_id)
- `attribute_name` VARCHAR(100) NOT NULL
- `attribute_value` TEXT - JSON or string value
- PRIMARY KEY (`business_id`, `attribute_name`)

**Design Decisions:**
- Accommodates nested JSON attributes (e.g., BusinessParking)
- TEXT allows complex values
- Trade-off: Harder to query specific nested values

**Indexes:**
- Composite primary key on `(business_id`, `attribute_name`)
- Optional GIN index on `attribute_value` for JSON queries (PostgreSQL)

#### 5. `users`
User profile information.

**Columns:**
- `user_id` VARCHAR(22) PRIMARY KEY
- `name` VARCHAR(255) - User's display name
- `review_count` INTEGER - Number of reviews written
- `yelping_since` DATE - Join date
- `useful` INTEGER - Useful votes sent
- `funny` INTEGER - Funny votes sent
- `cool` INTEGER - Cool votes sent
- `fans` INTEGER - Number of fans
- `average_stars` DECIMAL(3, 2) - Average rating given
- `compliment_hot` INTEGER
- `compliment_more` INTEGER
- `compliment_profile` INTEGER
- `compliment_cute` INTEGER
- `compliment_list` INTEGER
- `compliment_note` INTEGER
- `compliment_plain` INTEGER
- `compliment_cool` INTEGER
- `compliment_funny` INTEGER
- `compliment_writer` INTEGER
- `compliment_photos` INTEGER

**Design Decisions:**
- Denormalized compliment fields for query performance
- DATE type for yelping_since enables temporal queries
- DECIMAL for average_stars maintains precision

**Indexes:**
- Primary key on `user_id`
- B-tree index on `review_count` for top reviewers
- B-tree index on `fans` for influential users
- B-tree index on `yelping_since` for cohort analysis

#### 6. `user_friends`
Social graph of user friendships.

**Columns:**
- `user_id` VARCHAR(22) REFERENCES users(user_id)
- `friend_id` VARCHAR(22) REFERENCES users(user_id)
- PRIMARY KEY (`user_id`, `friend_id`)

**Design Decisions:**
- Bidirectional edges stored once (user_id < friend_id)
- Enables social network analysis
- Large table (~3M+ rows expected)

**Indexes:**
- Composite primary key on `(user_id, friend_id)`
- B-tree index on `friend_id` for reverse lookups

#### 7. `user_elite_years`
Years user achieved elite status.

**Columns:**
- `user_id` VARCHAR(22) REFERENCES users(user_id)
- `year` SMALLINT NOT NULL
- PRIMARY KEY (`user_id`, `year`)

**Design Decisions:**
- Normalized array into rows
- SMALLINT for year (saves space)

**Indexes:**
- Composite primary key on `(user_id, year)`

#### 8. `reviews`
Full review text and metadata.

**Columns:**
- `review_id` VARCHAR(22) PRIMARY KEY
- `user_id` VARCHAR(22) REFERENCES users(user_id)
- `business_id` VARCHAR(22) REFERENCES businesses(business_id)
- `stars` SMALLINT NOT NULL - Rating (1-5)
- `date` DATE NOT NULL - Review date
- `text` TEXT NOT NULL - Review content
- `useful` INTEGER DEFAULT 0
- `funny` INTEGER DEFAULT 0
- `cool` INTEGER DEFAULT 0

**Design Decisions:**
- Largest table (~7M rows)
- TEXT for unbounded review length
- Foreign keys ensure referential integrity
- Vote counts as integers with defaults

**Indexes:**
- Primary key on `review_id`
- B-tree index on `business_id` for business reviews
- B-tree index on `user_id` for user reviews
- B-tree index on `date` for temporal queries
- Composite index on `(business_id, date)` for recent reviews
- Full-text index on `text` for keyword search (optional)

#### 9. `tips`
Short suggestions from users.

**Columns:**
- `tip_id` SERIAL PRIMARY KEY - Auto-generated ID
- `user_id` VARCHAR(22) REFERENCES users(user_id)
- `business_id` VARCHAR(22) REFERENCES businesses(business_id)
- `text` TEXT NOT NULL
- `date` DATE NOT NULL
- `compliment_count` INTEGER DEFAULT 0

**Design Decisions:**
- Tips have no natural ID, use SERIAL
- Similar structure to reviews but shorter
- Compliment count instead of vote breakdown

**Indexes:**
- Primary key on `tip_id`
- B-tree index on `business_id`
- B-tree index on `user_id`
- B-tree index on `date`

#### 10. `checkins`
Aggregated check-in timestamps.

**Columns:**
- `checkin_id` SERIAL PRIMARY KEY
- `business_id` VARCHAR(22) REFERENCES businesses(business_id)
- `checkin_time` TIMESTAMP NOT NULL

**Design Decisions:**
- Explode comma-separated timestamps into rows
- Enables time-series analysis
- TIMESTAMP with timezone for accuracy

**Indexes:**
- Primary key on `checkin_id`
- B-tree index on `business_id`
- B-tree index on `checkin_time`
- Composite index on `(business_id, checkin_time)` for patterns

## Normalization Strategy

### 3NF Compliance
- All non-key attributes depend on the key, the whole key, and nothing but the key
- Categories, hours, and attributes extracted to separate tables
- User friends and elite years normalized

### Denormalization Decisions
- `review_count` and `stars` kept in `businesses` (updated via triggers or batch jobs)
- User compliment fields kept in `users` table (11 columns)
- Trade-off: Query performance vs. update complexity

## Data Type Rationale

| Type | Usage | Reason |
|------|-------|--------|
| VARCHAR(22) | Yelp IDs | Fixed-length, efficient indexing |
| TEXT | Reviews, tips | Unbounded length |
| DECIMAL | Stars, coordinates | Exact numeric precision |
| INTEGER | Counts | Standard numeric type |
| SMALLINT | 0/1 flags, years | Space-efficient |
| DATE | Dates without time | Temporal queries |
| TIMESTAMP | Check-ins | Full datetime precision |

## Index Strategy

### Primary Keys
All tables have primary keys for uniqueness and clustering.

### Foreign Keys
Enforce referential integrity between:
- reviews → users, businesses
- tips → users, businesses
- checkins → businesses
- business_* → businesses
- user_* → users

### Query Optimization Indexes

**Business queries:**
- `(city, state)` - Location filtering
- `stars` - Rating-based sorting
- `(latitude, longitude)` - Spatial searches

**Review queries:**
- `(business_id, date)` - Recent reviews per business
- `date` - Temporal analysis
- `text` (full-text) - Keyword search

**User queries:**
- `review_count`, `fans` - Top users
- `yelping_since` - Cohort analysis

**Social queries:**
- `(user_id, friend_id)` - Friend lookup
- `friend_id` - Reverse friend lookup

### Index Maintenance
- B-tree indexes for equality and range queries
- GIN indexes for JSON and full-text search
- Partial indexes for frequently filtered subsets (e.g., `is_open = 1`)

## Performance Considerations

### Large Tables
- **reviews**: ~7M rows - Partition by date or business_id if queries slow
- **users**: ~2M rows - Manageable with proper indexing
- **user_friends**: ~3M+ rows - Consider graph database for complex social queries

### Query Patterns
- Top-k queries need `LIMIT k` to avoid full scans
- Join optimization via foreign key indexes
- Text search may need dedicated tools (Elasticsearch) for large scale

### Import Strategy
- Use `COPY` command for bulk inserts (100x faster than INSERT)
- Disable indexes during import, rebuild after
- Batch size: 10,000 rows per transaction
- Parallelize table imports (business, user, review independent)

## Next Steps

1. Review this schema design
2. Implement `create_tables.sql` with DDL statements
3. Implement `create_indexes.sql` with index definitions
4. Create ER diagram visualization
5. Proceed to data import phase

# Yelp Dataset Query Workflow

Data engineering project for the Yelp academic dataset using PostgreSQL and Python.

**Tech Stack:** Python 3.10+, PostgreSQL 17, Poetry, Docker

## Quick Start

### 1. Start Database
```bash
docker compose up -d
```

### 2. Install Dependencies
```bash
poetry install
```

### 3. Initialize Schema
```bash
poetry run python scripts/init_db.py
```

### 4. Import Data

Place Yelp dataset files in `yelp_dataset/` directory, then run:

```bash
poetry run python import/import_data.py
```

Expected import time: **~12-15 minutes** (optimized with PostgreSQL COPY)

### 5. View Schema
```bash
poetry run python scripts/view_schema.py counts
```

## Project Structure

```
.
├── docker-compose.yml          # PostgreSQL 17 (port 5433)
├── pyproject.toml             # Dependencies
├── .env                       # Database credentials
│
├── schema/
│   ├── create_tables.sql      # Table definitions
│   └── create_indexes.sql     # Index definitions
│
├── scripts/
│   ├── init_db.py            # Initialize schema
│   └── view_schema.py        # View tables/counts
│
├── import/
│   ├── import_data.py        # Optimized import script
│   └── test_review_data.py  # Data validation test
│
└── queries/
    └── query_functions.py    # Query implementations (TODO)
```

## Database Schema

**10 normalized tables:**
- `businesses` (150K rows)
- `users` (2M rows)
- `reviews` (7M rows)
- `tips` (1M rows)
- `checkins` (3M rows)
- `business_categories`, `business_hours`, `business_attributes`
- `user_friends`, `user_elite_years`

**37 indexes** for query optimization

## Environment Variables

Create `.env` file:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=yelp
DB_USER=postgres
DB_PASSWORD=postgres
```

## Database Commands

```bash
# Start database
docker compose up -d

# Stop database
docker compose down

# Reset database (delete all data)
docker compose down -v
poetry run python scripts/init_db.py

# Access PostgreSQL CLI
docker compose exec postgres psql -U postgres -d yelp
```

## Import Optimizations

The import script includes:
- **PostgreSQL COPY** for reviews (10-50x faster than INSERT)
- **Large batch sizes** (50K-100K rows)
- **In-memory FK validation** (3000x faster for friendships)
- **Automatic skipping** of invalid foreign key references

## Performance

| Table | Rows | Import Time |
|-------|------|-------------|
| businesses | 150K | ~1 min |
| users | 2M | ~2 min |
| user_friends | varies | ~2-3 min |
| reviews | 7M | ~2-3 min |
| tips | 1M | ~1 min |
| checkins | 3M | ~2 min |
| **TOTAL** | **~13M** | **~12-15 min** |

## Notes

- Dataset files (9GB) are **NOT** committed to repository
- Port 5433 used to avoid conflicts with system PostgreSQL
- All imports validate foreign keys to prevent constraint violations

## Author

Sungchunn

# Yelp Dataset Query Workflow

Data engineering project implementing database ingestion, schema design, and optimized queries for the Yelp academic dataset.

## Project Overview

This project demonstrates a complete data engineering workflow:
- Designing a normalized database schema (3NF)
- Importing large datasets efficiently (~9GB)
- Implementing optimized SQL queries
- Conducting index ablation studies

**Tech Stack:** Python 3.10+, PostgreSQL 17, Poetry, Docker

## Prerequisites

- Docker & Docker Compose
- Python 3.10 or higher
- Poetry (dependency manager)
- Yelp Academic Dataset (download from Canvas)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd dataeng_a1
```

### 2. Start PostgreSQL Database

```bash
docker compose up -d
```

This starts PostgreSQL 17 on port **5433** (to avoid conflicts with system PostgreSQL).

### 3. Install Python Dependencies

```bash
poetry install
```

### 4. Configure Environment

Create a `.env` file (or use the existing one):

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=yelp
DB_USER=postgres
DB_PASSWORD=postgres
```

### 5. Initialize Database Schema

```bash
poetry run python scripts/init_db.py
```

This creates:
- 10 normalized tables
- 37 indexes (10 primary keys + 27 secondary)
- Foreign key constraints
- Check constraints

### 6. Verify Connection

```bash
poetry run python test_connection.py
```

Expected output:
```
✅ Database connection successful!
PostgreSQL version: PostgreSQL 17.6 ...
```

## Project Structure

```
.
├── docker-compose.yml          # PostgreSQL 17 setup
├── pyproject.toml             # Poetry dependencies
├── README.md                  # This file
├── .env                       # Database credentials (not committed)
│
├── schema/
│   ├── claude.md              # Schema design rationale
│   ├── create_tables.sql      # Table DDL
│   └── create_indexes.sql     # Index definitions
│
├── scripts/
│   └── init_db.py             # Schema initialization script
│
├── import/
│   ├── claude.md              # Import strategy guide
│   └── import_data.py         # Data import script (to be implemented)
│
├── queries/
│   ├── claude.md              # Query implementation guide
│   └── query_functions.py     # Query functions (to be implemented)
│
├── experiments/
│   ├── claude.md              # Ablation study guide
│   ├── run_experiment.py      # Timing experiments (to be implemented)
│   └── results.md             # Timing results (to be created)
│
└── docs/
    ├── schema_diagram.md      # ER diagram
    └── indexes.md             # Index documentation
```

## Database Schema

The database consists of 10 normalized tables:

### Core Tables
- **businesses** - Business information (150K rows expected)
- **users** - User profiles (2M rows expected)
- **reviews** - Full review text (7M rows expected)

### Relationship Tables
- **business_categories** - Many-to-many categories
- **business_hours** - Operating hours by day
- **business_attributes** - Flexible key-value attributes
- **user_friends** - Social network graph
- **user_elite_years** - Elite status tracking
- **tips** - Short suggestions
- **checkins** - Timestamped check-ins

See `docs/schema_diagram.md` for full ER diagram.

## Data Import

**⚠️ Important:** Dataset files are NOT committed to the repository (9GB total).

Place the Yelp dataset in `yelp_dataset/` directory:
```
yelp_dataset/
├── yelp_academic_dataset_business.json
├── yelp_academic_dataset_review.json
├── yelp_academic_dataset_user.json
├── yelp_academic_dataset_checkin.json
└── yelp_academic_dataset_tip.json
```

### Run Import

```bash
poetry run python import/import_data.py
```

Expected time: ~20-30 minutes with optimizations.

See `import/claude.md` for detailed import strategy.

## Query Functions

Five required query functions (to be implemented):

1. **still_there(state)** - Top 9 open businesses by review count
2. **top_reviews(business_id)** - Top 7 most useful reviews
3. **average_rating(user_id)** - User's average star rating
4. **topBusiness_in_city(city, elite_count, top_count)** - Businesses with elite reviews
5. **high_fives(city, top_count)** - Highest percentage of 5-star reviews

All queries optimized to execute in <1 second.

### Run Queries

```bash
poetry run python queries/query_functions.py
```

## Index Ablation Study

Measures query performance with and without indexes.

### Run Experiment

```bash
poetry run python experiments/run_experiment.py
```

Results saved to `experiments/results.md`.

Expected findings: 50-200x speedup with proper indexing.

## Database Management

### Start Database
```bash
docker compose up -d
```

### Stop Database
```bash
docker compose down
```

### Reset Database (Delete All Data)
```bash
docker compose down -v
poetry run python scripts/init_db.py
```

### View Logs
```bash
docker compose logs -f postgres
```

### Access PostgreSQL CLI
```bash
docker compose exec postgres psql -U postgres -d yelp
```

Useful commands:
- `\dt` - List tables
- `\d+ businesses` - Describe table
- `\di` - List indexes
- `\q` - Quit

## Development

### Add Dependencies
```bash
poetry add <package-name>
```

### Run Tests
```bash
poetry run pytest
```

### Format Code
```bash
poetry run black .
poetry run isort .
```

## Git Workflow

⚠️ **Do NOT commit:**
- Dataset files (`yelp_dataset/`)
- Database files (`.db/`, volumes)
- Environment files (`.env`)
- Lock files (`poetry.lock`)

These are excluded in `.gitignore`.

## Performance Benchmarks

| Table | Rows | Import Time | Query Time (avg) |
|-------|------|-------------|------------------|
| businesses | 150K | ~30s | <10ms |
| users | 2M | ~2min | <10ms |
| reviews | 7M | ~10-15min | <100ms |
| tips | 1M | ~1min | <50ms |
| checkins | 3M | ~5min | <50ms |

## Troubleshooting

### Port 5432 Already in Use
Solution: We use port 5433. If still having issues:
```bash
docker compose down
# Edit docker-compose.yml to change port
docker compose up -d
```

### Cannot Connect to Database
```bash
# Check container is running
docker compose ps

# Check logs
docker compose logs postgres

# Verify .env file exists and has correct credentials
cat .env
```

### Import Taking Too Long
- Ensure indexes are created AFTER import (or use drop/recreate strategy)
- Check batch size (should be 10,000)
- Verify using COPY or execute_batch (not individual INSERTs)

### Query Timeout
- Verify indexes are created: `docker compose exec postgres psql -U postgres -d yelp -c "\di"`
- Check query plan: `EXPLAIN ANALYZE <query>`
- Ensure statistics are updated: `ANALYZE <table>`

## Documentation

- **Schema Design:** `schema/claude.md`
- **ER Diagram:** `docs/schema_diagram.md`
- **Index Strategy:** `docs/indexes.md`
- **Import Guide:** `import/claude.md`
- **Query Guide:** `queries/claude.md`
- **Ablation Study:** `experiments/claude.md`

## License

Academic project for coursework.

## Authors

- Sungchunn

## Acknowledgments

- Yelp Dataset: https://www.yelp.com/dataset
- PostgreSQL Documentation: https://www.postgresql.org/docs/

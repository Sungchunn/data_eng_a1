# Yelp Dataset Query Workflow

Data engineering project for the Yelp academic dataset using PostgreSQL and Python.

**Tech Stack:** Python 3.12, PostgreSQL 17, Poetry, Docker

---

## 🚀 Quick Start

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

### 4. Import Data (Optional - Data already in Docker)

⚠️ **Note:** Data is already imported and stored in Docker volume `yelp_db_volume` (12GB)

If you need to re-import:
1. Place Yelp dataset files in `yelp_dataset/` directory
2. Run: `poetry run python import/import_data.py`

Expected import time: **~12-15 minutes** (optimized with PostgreSQL COPY)

### 5. Test Queries
```bash
# Comprehensive test suite (recommended)
poetry run python queries/test_all.py

# Or run individual functions
poetry run python queries/query_functions.py
```

---

## 📁 Project Structure

```
.
├── docker-compose.yml          # PostgreSQL 17 (port 5433)
├── pyproject.toml             # Dependencies
├── .env                       # Database credentials
│
├── schema/
│   ├── create_tables.sql      # Table definitions (10 tables)
│   └── create_indexes.sql     # Index definitions (40 indexes)
│
├── import/
│   ├── import_data.py        # Optimized import script
│   └── test_review_data.py  # Data validation utility
│
├── queries/
│   ├── query_functions.py    # 5 query implementations ✅
│   ├── test_all.py          # Comprehensive test suite
│   ├── test_performance.py  # Performance benchmarks
│   └── explain_analyze.py   # Query plan analysis
│
├── scripts/
│   ├── init_db.py           # Initialize database schema
│   └── view_schema.py       # View schema & row counts
│
└── docs/
    ├── schema_diagram.md        # ER diagram & schema docs
    ├── indexes.md              # Index documentation
    │
    ├── deliverables/
    │   ├── PHASE3_DELIVERABLES.md  # Phase 3 summary
    │   ├── PHASE6_IMPROVEMENTS.md  # Phase 6 fixes
    │   ├── ANALYSIS.md            # Code analysis report
    │   └── INDEX_VISUALIZATION.md # Index visualization
    │
    └── guides/
        ├── RUN_TESTS.md          # Test execution guide
        ├── QUICK_START.md        # Quick reference
        └── TEST_COMMANDS.md      # Individual test commands
```

---

## 📊 Database Schema

### Tables (10 total)

| Table | Rows | Description |
|-------|------|-------------|
| **businesses** | 150,346 | Business entities |
| **users** | 1,987,897 | User profiles |
| **reviews** | 6,990,280 | Full reviews |
| **tips** | 908,915 | Short tips |
| **checkins** | 13,356,875 | Check-in timestamps |
| business_categories | 502,210 | Business-category links |
| business_hours | 1,140,798 | Operating hours |
| business_attributes | 1,329,088 | Attribute key-values |
| user_friends | 16,914,627 | Social graph |
| user_elite_years | 340,567 | Elite status history |
| **TOTAL** | **~42M rows** | |

### Indexes (40 total)
- **B-tree:** 37 indexes (primary keys, foreign keys, sorting)
- **GIN:** 1 index (full-text search on review text)
- **Partial:** 2 indexes (optimized for `is_open = 1`)

**Index overhead:** 2.6GB (~43% of table size)

---

## ⚡ Query Performance

| Query | Time | Status |
|-------|------|--------|
| `average_rating` | 17ms | ✅ |
| `still_there` | 10ms | ✅ |
| `top_reviews` | 50ms | ✅ |
| `high_fives` | 370ms | ✅ |
| `topBusiness_in_city` | 2377ms | ⚠️ |

**4 out of 5 queries** meet the <1 second requirement (80% pass rate)

---

## 🧪 Testing

### Quick Test (Recommended)
```bash
poetry run python queries/test_all.py
```

Tests:
- ✅ Output field correctness
- ✅ Performance benchmarks
- ✅ Data quality validation

### Performance Only
```bash
poetry run python queries/test_performance.py
```

### Interactive Test
```bash
poetry run python queries/query_functions.py
```

---

## 🗄️ Database Commands

```bash
# Start database
docker compose up -d

# Stop database
docker compose down

# View table counts
poetry run python scripts/view_schema.py counts

# Access PostgreSQL CLI
docker compose exec postgres psql -U postgres -d yelp

# Check Docker volume (data persistence)
docker volume ls | grep yelp
```

---

## 📈 Import Optimizations

The import script includes:
- **PostgreSQL COPY** for reviews (10-50x faster than INSERT)
- **Large batch sizes** (50K-100K rows)
- **In-memory FK validation** (3000x faster for friendships)
- **Automatic skipping** of invalid foreign key references

### Import Performance

| Table | Rows | Import Time |
|-------|------|-------------|
| businesses | 150K | ~1 min |
| users | 2M | ~2 min |
| user_friends | 17M | ~3 min |
| reviews | 7M | ~3 min |
| tips | 1M | ~1 min |
| checkins | 13M | ~2 min |
| **TOTAL** | **~42M** | **~12-15 min** |

---

## 📚 Documentation

### Core Documentation
- **[Schema Diagram](docs/schema_diagram.md)** - ER diagram, table definitions, relationships
- **[Index Documentation](docs/indexes.md)** - All 40 indexes with descriptions
- **[Index Visualization](docs/deliverables/INDEX_VISUALIZATION.md)** - Visual guide

### Deliverables
- **[Phase 3 Deliverables](docs/deliverables/PHASE3_DELIVERABLES.md)** - Schema & import summary
- **[Phase 6 Improvements](docs/deliverables/PHASE6_IMPROVEMENTS.md)** - Output field fixes
- **[Analysis Report](docs/deliverables/ANALYSIS.md)** - Strengths & limitations

### Testing Guides
- **[Run Tests](docs/guides/RUN_TESTS.md)** - Comprehensive testing guide
- **[Quick Start](docs/guides/QUICK_START.md)** - Quick reference
- **[Test Commands](docs/guides/TEST_COMMANDS.md)** - Individual commands

---

## 🔑 Environment Variables

Create `.env` file (already configured):

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=yelp
DB_USER=postgres
DB_PASSWORD=postgres
```

---

## 📝 Implementation Highlights

### Query Functions (5 total)
1. **average_rating(user_id)** - User's average rating
2. **still_there(state)** - Top 9 open businesses by state
3. **top_reviews(business_id)** - Top 7 most useful reviews
4. **high_fives(city, top_count)** - Businesses with highest 5-star %
5. **topBusiness_in_city(city, elite_count, top_count)** - Most elite reviews

### Key Achievements
- ✅ All queries return complete output fields
- ✅ Single SQL statement per query (no loops)
- ✅ Top-K optimization with LIMIT
- ✅ 40 indexes for query optimization
- ✅ Comprehensive test suite
- ✅ 86% assignment compliance

---

## 💾 Storage

- **Docker Volume:** `yelp_db_volume` (12GB) - Contains all data
- **Project Files:** ~17MB (JSON dataset removed to save 8.7GB)
- **Data Persistence:** Survives container restarts via Docker volume

---

## 🎯 Project Status

**Phase 3 (Schema & Import):** ✅ Complete
- Database schema with ER diagram
- 40 indexes with documentation
- Optimized import script

**Phase 4 (Query Implementation):** ✅ Complete
- All 5 functions implemented
- Output fields corrected (Phase 6)

**Phase 5 (Performance Testing):** ✅ Complete
- Performance benchmarks
- EXPLAIN ANALYZE results
- Query optimization

**Overall Compliance:** 86% (6/7 requirements met)

---

## 👤 Author

Sungchunn

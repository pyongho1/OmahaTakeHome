## EcoVision: Climate Visualizer — Documentation

### Overview
- **Goal**: Provide a small, working climate data API (Flask + MySQL) with filters, summaries, and basic trends, and a React frontend to visualize results.
- **Design**: Simple, readable SQL and optional filters; environment-based configuration; 1-decimal rounding for user-facing values.

### Stack and architecture
- **Backend**: Flask + `flask_mysqldb` (MySQL), CORS enabled
- **Database**: MySQL 8 (Docker Compose)
- **Frontend**: React + Vite + TailwindCSS (proxy to backend)
- **Config**: `.env` for DB credentials (loaded by `python-dotenv`)

---

## Setup

### Prerequisites
- Python 3.x, Node.js 18+
- Docker Desktop
- Ensure `python-dotenv` is installed in your backend venv

### Environment variables (`backend/.env`)
```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=ecouser
MYSQL_PASSWORD=ecopass
MYSQL_DB=ecovision
MYSQL_CURSORCLASS=DictCursor
```
- Keep values unquoted; do not prefix with `export`.

### Install dependencies
```bash
# Backend (create/activate venv and install)
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
```

### Start services
```bash
# MySQL
docker compose up -d

# Seed database
cd backend
python3 seed.py

# Run backend
python3 app.py

# Run frontend (separate terminal)
cd frontend
npm run dev
```
- Frontend at `http://localhost:3000` (proxy to `http://localhost:5000`).

---

## Data model

Tables and important fields (InnoDB with FKs):
- **`locations`**: `id`, `name`, `country`, `latitude`, `longitude`, `region`
- **`metrics`**: `id`, `name`, `display_name`, `unit`, `description`
- **`climate_data`**: `id`, `location_id` (FK), `metric_id` (FK), `date`, `value`, `quality`

Quality levels are ranked: `poor` < `questionable` < `good` < `excellent`.

---

## Seeding

- Source file: `data/sample_data.json` (valid JSON; no comments)
- Script: `backend/seed.py`
- Creates tables if needed, inserts `locations`, `metrics`, then `climate_data`
- Idempotent via `ON DUPLICATE KEY UPDATE`
- Uses `backend/.env` for DB connection

---

## API

### Base URL
- `http://localhost:5000/api/v1/`

### Shared query parameters
- **`location_id`**: optional, integer
- **`start_date`**, **`end_date`**: optional, `YYYY-MM-DD`
- **`metric`**: optional, string (e.g., `temperature`, `precipitation`, `humidity`)
- **`quality_threshold`**: optional, one of `poor|questionable|good|excellent`
  - Uses MySQL `FIELD` to keep rows with quality rank ≥ threshold.
- Pagination (when used): `page` (default 1), `per_page` (default 50)

### Endpoints

#### GET `/api/v1/locations`
- Returns list of locations.
```json
{ "data": [{ "id": 1, "name": "Irvine", "country": "USA", "latitude": 33.68, "longitude": -117.83 }] }
```

#### GET `/api/v1/metrics`
- Returns list of metrics.
```json
{ "data": [{ "id": 1, "name": "temperature", "display_name": "Temperature", "unit": "celsius" }] }
```

#### GET `/api/v1/climate`
- Returns climate records with optional filters. Simple version uses a single SQL with “param IS NULL OR condition”.
- Response fields include `location_name`, `latitude`, `longitude`, `metric`, `unit`, `value`, `quality`, `date`.
- Values and dates are normalized (date as `YYYY-MM-DD`).

Example (shape):
```json
{
  "data": [
    {
      "id": 1,
      "location_id": 123,
      "location_name": "New York",
      "latitude": 40.7128,
      "longitude": -74.006,
      "date": "2023-01-01",
      "metric": "temperature",
      "value": 3.5,
      "unit": "celsius",
      "quality": "good"
    }
  ],
  "meta": { "total_count": 1, "page": 1, "per_page": 1 }
}
```

#### GET `/api/v1/summary`
- Per-metric aggregates with filters:
  - `min`, `max`, `avg`, `weighted_avg` (weights: excellent=1.0, good=0.8, questionable=0.5, poor=0.3)
  - `quality_distribution` (fractions per quality level)
- Aggregates rounded to 1 decimal; distribution fractions rounded to 1 decimal.

Example (shape):
```json
{
  "data": {
    "temperature": {
      "min": -5.2,
      "max": 35.9,
      "avg": 15.7,
      "weighted_avg": 14.2,
      "unit": "celsius",
      "quality_distribution": {
        "excellent": 0.3,
        "good": 0.5,
        "questionable": 0.1,
        "poor": 0.1
      }
    }
  }
}
```

#### GET `/api/v1/trends`
- Per metric:
  - **trend**: direction (`increasing|decreasing|stable`), rate (units/month), confidence (|Pearson r|)
  - **anomalies**: points with z-score > 2 (report date, value, deviation, quality)
  - **seasonality**: seasonal averages for winter/spring/summer/fall, simple confidence and trend hints
- Numeric outputs rounded to 1 decimal where appropriate.

Example (shape):
```json
{
  "data": {
    "temperature": {
      "trend": { "direction": "increasing", "rate": 0.5, "unit": "celsius/month", "confidence": 0.85 },
      "anomalies": [{ "date": "2023-06-15", "value": 42.1, "deviation": 2.5, "quality": "excellent" }],
      "seasonality": {
        "detected": true,
        "period": "yearly",
        "confidence": 0.92,
        "pattern": {
          "winter": { "avg": 5.2, "trend": "stable" },
          "spring": { "avg": 15.7, "trend": "increasing" },
          "summer": { "avg": 25.3, "trend": "increasing" },
          "fall": { "avg": 18.1, "trend": "stable" }
        }
      }
    }
  }
}
```

---

## Implementation details

### Optional-filter pattern
- Keep one static SQL and pass parameters twice: `(? IS NULL OR column = ?)` avoids dynamic SQL while supporting optional filters.

### Quality threshold filter
- Uses MySQL `FIELD` to rank levels:
```sql
FIELD(cd.quality, 'poor','questionable','good','excellent')
  >= FIELD(?, 'poor','questionable','good','excellent')
```

### Rounding
- Aggregates and user-facing values rounded to 1 decimal:
  - In SQL: `ROUND(AVG(value), 1)` or `ROUND(weighted_avg, 1)`
  - In Python (if needed): `round(x, 1)`

### Trend logic
- Linear regression slope (units/month) using month index; confidence ≈ |Pearson r|.
- Anomalies by z-score > 2.
- Seasonality: month-of-year averages collapsed into seasons; simple range-based heuristic for detection and confidence.

---

## Troubleshooting

- **`.env` not loaded**:
  - Ensure it’s in `backend/.env`.
  - Load with `load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)`.
  - No quotes or `export` in `.env`. Set `MYSQL_PORT` as integer-like text.

- **JSON parse error in seed**:
  - JSON does not allow comments. Remove any `//` comments from `data/sample_data.json`.

- **Foreign key errors on seed**:
  - Ensure `locations` and `metrics` are inserted before `climate_data`.
  - If partial data exists, truncate tables (with FK checks off) and re-seed.

- **Driver/version issues**:
  - `flask_mysqldb` requires a Flask version compatible with its internals. Use the versions pinned in `backend/requirements.txt`.
  - Ensure `mysqlclient` (MySQLdb) is installed in your backend venv.

---

## Project structure
- `backend/app.py`: Flask app, endpoints, MySQL config
- `backend/seed.py`: Table creation + data seeding from `data/sample_data.json`
- `backend/.env`: DB credentials (loaded by backend and seeder)
- `docker-compose.yml`: MySQL 8 service
- `frontend/`: React + Vite app (proxy configured)
- `docs/`: API and schema documents

---

## Future improvements
- Add OpenAPI docs and request validation
- Pagination and caching for large datasets
- More robust trend/seasonality modeling
- Configurable quality weights per request
- Index tuning and performance testing with larger data



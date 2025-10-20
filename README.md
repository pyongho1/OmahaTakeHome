# Take Home Assessment — EcoVision: Climate Visualizer

This project assesses full‑stack skills (Python, JavaScript, SQL) by building an interactive climate data explorer.

See the full docs: `docs/documentation.md`.

## Prerequisites
- Python 3.x
- Node.js 18+ and npm
- Docker Desktop (for MySQL)

## Quick Start

### 1) Backend setup (virtualenv + deps)
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 2) Database (MySQL via Docker)
A `docker-compose.yml` is provided at the repo root. Start MySQL:
```bash
docker compose up -d
```

Recommended environment variables for the backend (match compose file):
```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_USER=ecouser
export MYSQL_PASSWORD=ecopass
export MYSQL_DB=ecovision
```

### 3) Run the backend (Flask)
```bash
python backend/app.py
```
- Base URL: `http://localhost:5000/api/v1/`
- Endpoints to implement: see `docs/api.md`

### 4) Frontend (Vite + React)
```bash
cd frontend
npm install
npm run dev
```
- App: `http://localhost:3000`
- Proxy to backend is preconfigured in `frontend/vite.config.js`

## Data & Schema
- Sample data: `data/sample_data.json`
- Database guidance: `docs/schema.md`
- You’ll need to design tables and seed the DB to support the API.

## Documentation
- API spec and example responses: `docs/api.md`
- Schema guidance: `docs/schema.md`

## Project Structure
- `backend/app.py`: Flask API scaffold (CORS, MySQL config via env)
- `frontend/`: React + Vite + Tailwind UI scaffold
- `data/sample_data.json`: Example data for seeding
- `docker-compose.yml`: MySQL 8.0 service
- `docs/`: API spec and schema notes

## Notes
- Ensure your backend env vars match the Docker MySQL settings (`MYSQL_DB=ecovision`, etc.).
- The provided endpoints in `backend/app.py` are placeholders; implement per `docs/api.md`.
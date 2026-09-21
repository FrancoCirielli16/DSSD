# RescueSync (DSSD)

Stack Entrega 2 (en progreso): **FastAPI** + **React/Vite** + **PostgreSQL (Docker)**.

## HU-2.1 — PostgreSQL con Docker

Puerto host **5433** (evita choque si ya tenés Postgres en 5432).

```bash
docker compose up -d
docker exec rescuesync-db pg_isready -U rescuesync -d rescuesync
```

URL: `postgresql://rescuesync:rescuesync@localhost:5433/rescuesync`

## Backend (FastAPI)

```bash
cd backend
copy .env.example .env
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/docs  
Usuarios seed (clave `bpm`): `operador.municipal`, `coordinador.regional`, `ong.cruzroja`, `ong.bomberos`

## Frontend (React + Vite)

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

App: http://localhost:5173

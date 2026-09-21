# RescueSync (DSSD)

## HU-2.1 — PostgreSQL con Docker

Puerto host **5433** (evita choque si ya tenés Postgres en 5432).

```bash
docker compose up -d
docker compose ps
docker exec rescuesync-db pg_isready -U rescuesync -d rescuesync
```

Credenciales:
- user / password / db: `rescuesync`
- URL: `postgresql://rescuesync:rescuesync@localhost:5433/rescuesync`

Para bajarlo: `docker compose down` (los datos quedan en el volume `rescuesync_pg`).

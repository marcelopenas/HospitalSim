# Getting started

## Dashboard without a backend

Install Node.js 24 and npm, then run from the repository root:

```bash
cd web
npm ci
npm run dev
```

Open Vite's printed URL, normally http://localhost:5173. No login or database setup is needed. The top **Documentation** link opens this project's GitHub Pages documentation; **Swagger API** opens the local backend's `/docs` page if that service is running.

## Full stack with Docker

Install Docker and Compose v2. From the repository root:

```bash
cp .env.example .env
# Edit .env to review development passwords and other settings.
docker compose up --build
```

**`bash run.sh` deliberately deletes the project's Compose volumes and all MySQL API records**, then rebuilds a clean instance. This is intentional for repeatable development and demonstrations. It exports `requirements.txt` with uv and creates `.env` from the example when missing. `bash run.sh -d` performs the same reset in the background. To preserve records, use `docker compose down` followed by `docker compose up --build` instead. Browser-local demo progress is separate; reset it in the dashboard.

| Component | URL |
| --- | --- |
| Dashboard | http://localhost:3000 |
| Swagger | http://localhost:8080/docs |
| ReDoc | http://localhost:8080/redoc |
| OpenAPI JSON | http://localhost:8080/openapi.json |
| Health | http://localhost:8080/health |

The database may take a short time to initialize. Compose waits for MySQL to respond before starting the API. SQLModel creates missing tables at API startup. The API database is initially empty; frontend data is seeded independently.

```bash
docker compose ps
docker compose logs -f web
docker compose down
```

`docker compose down` preserves the `db-data` volume. To rebuild the web dashboard after changing its source or build variables, run `docker compose up --build frontend`.

## Local Python development

The declared minimum is Python 3.14. Install uv, supply an accessible MySQL database and user, then run:

```bash
uv sync --locked
export DATABASE_URL='mysql+pymysql://hospitalsim:YOUR_PASSWORD@localhost:3306/hospitalsim'
uv run fastapi dev app/main.py --port 8080
```

The API does not automatically load `.env`. Export the connection string in the process environment. The default Compose database has no host port mapping, so local Python cannot reach that database at `localhost:3306` unless you explicitly add a mapping. Use a local MySQL server or a Compose override for that development mode.

## Environment configuration

| Variable | Meaning |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy/PyMySQL URL; required when starting Python directly |
| `MYSQL_DATABASE` | Database created by the MySQL container on first initialization |
| `MYSQL_USER` / `MYSQL_PASSWORD` | Application database user, distinct from root |
| `MYSQL_ROOT_PASSWORD` | MySQL root initialization password |
| `SQL_ECHO` | `true` enables SQL logging; defaults to false |
| `VITE_SWAGGER_URL` | Optional public, build-time URL for the top Swagger link |

For Docker, root `.env` supplies Compose interpolation and the frontend build argument. For Vite development, put `VITE_SWAGGER_URL` in `web/.env.local`. The default Swagger link uses the browser hostname, HTTP, and port 8080. Set an explicit HTTPS URL when deploying over HTTPS. Never put secrets in `VITE_` variables.

Use URL-safe passwords or percent-encode special characters in a database URL. The example credentials are local development defaults. Existing MySQL volumes retain initialized users and passwords even after you edit `.env`; update database users explicitly when changing credentials.

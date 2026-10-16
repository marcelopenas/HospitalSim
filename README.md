# HospitalSim

An interactive hospital operations sandbox, backed by a separate FastAPI CRUD service and a relational MySQL database. Explore patient flow, department capacity, and care assignments in an English dashboard with no login.

[Project documentation](https://marcelopenas.github.io/HospitalSim/) · [Local dashboard](http://localhost:3000) · [Local Swagger UI](http://localhost:8080/docs)

## What you can do

- Switch between two fictional hospitals, each with independent simulation progress.
- Run or pause a seeded simulation, select normal operations, patient surge, or critical demand, change speed, and advance one simulated hour.
- Monitor active patients, bed occupancy, staffing, department capacity, admissions, discharges, and an activity feed.
- Admit synthetic patients, search and filter records, discharge patients, and observe waiting patients take newly available beds in their department.
- Inspect named clinicians, care roles, assignments, and hospital summaries.
- Open documentation and Swagger directly from the top navigation.
- Create, read, update, and delete hospital, role, staff, and patient records through the API.

**Data boundary:** the website is a self-contained browser simulation. Its records and metrics are synthetic and saved in this browser's local storage, independently of MySQL. It does not read or write API records. Swagger operates on the real API database. Department, bed, queue, and simulation data are frontend concepts, not fields in the existing backend schema. No authentication is implemented in either component; use synthetic data in a trusted development environment.

## Quick start: dashboard only

Requires Node.js 24 (matching the frontend Docker build) and npm.

```bash
cd web
npm ci
npm run dev
```

Open the URL printed by Vite (usually http://localhost:5173). The dashboard works without Python, Docker, or a database. Swagger requires the backend to be running.

## Quick start: full stack with Docker

Requires Docker Engine or Docker Desktop with Compose v2.

```bash
cp .env.example .env
# Review .env and change its local development passwords as needed.
docker compose up --build
```

Alternatively, `bash run.sh` creates `.env` from the example when missing and starts the stack. `bash run.sh -d` runs in the background. Existing database data is preserved.

| Service | Address | Purpose |
| --- | --- | --- |
| Dashboard | http://localhost:3000 | No-login browser simulation |
| Swagger UI | http://localhost:8080/docs | Interactive API requests |
| ReDoc | http://localhost:8080/redoc | Read-only API reference |
| OpenAPI schema | http://localhost:8080/openapi.json | Machine-readable API contract |
| Health | http://localhost:8080/health | Process health; returns `{"status":"ok"}` |

The API waits for MySQL readiness, then creates missing SQLModel tables on startup. The database starts empty; the browser demo has its own fixtures. MySQL uses a named `db-data` volume and is not exposed on a host port by the default Compose configuration.

```bash
docker compose logs -f web
# Stop services while retaining database records:
docker compose down
```

Deleting `db-data` erases API records. Do so only when you intentionally want a fresh database. Changing the `.env` MySQL credentials does not change users already stored in an existing volume.

## Local backend development

Python 3.14+ and [uv](https://docs.astral.sh/uv/) are required by `pyproject.toml`. Use an accessible MySQL instance and create the database and user before startup.

```bash
uv sync --locked
# Export a connection string for your local MySQL server:
export DATABASE_URL='mysql+pymysql://hospitalsim:YOUR_PASSWORD@localhost:3306/hospitalsim'
uv run fastapi dev app/main.py --port 8080
```

The API reads `DATABASE_URL` from the process environment; it does not load `.env` itself. Compose loads `.env` for variable interpolation and injects a container-specific connection string. Passwords containing URL-special characters must be URL-encoded in connection strings. The PyMySQL RSA extra supports MySQL's default password authentication.

The backend is a synchronous SQLModel application. `create_all` creates missing tables, but does not migrate existing tables. Introduce explicit migrations before changing a deployed schema.

## Website development and configuration

```bash
cd web
npm ci
npm run dev
npm test
npm run build
npm run preview
```

The production output is `web/dist/`, served by Nginx in Docker. Vite environment variables are public and embedded **at build time**, so frontend container runtime variables cannot change them.

| Variable | Default | Where to set it |
| --- | --- | --- |
| `VITE_SWAGGER_URL` | `http://<browser hostname>:8080/docs` | `web/.env.local` for local Vite; root `.env` for Compose builds |
| `DATABASE_URL` | Required by Python | Shell environment locally; supplied by Compose in Docker |
| `SQL_ECHO` | `false` | Shell environment or root `.env` |
| `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` | Values in `.env.example` for local use | Root `.env` for Compose |

For an HTTPS deployment or externally hosted API, set `VITE_SWAGGER_URL` to its actual HTTPS Swagger address and rebuild. No browser API requests are made by the dashboard, so CORS is not needed for this demo.

## Simulation guide

Start with **Run simulation**. At 1× speed, every three real seconds advances 15 simulated minutes; 2× and 4× shorten that interval. **+1 hour** immediately runs four steps. The simulation starts at Day 1, 08:00, and advances only while the page is open and running. Reloads start paused.

| Scenario | New patients per 15 simulated minutes |
| --- | --- |
| Normal operations | 1–3 |
| Patient surge | 4–6 |
| Critical demand | 7–9 |

Arrivals select one of four departments. A patient receives a bed when that department has capacity, otherwise joins its queue. Stays last 60–479 simulated minutes for new patients. Discharges free beds for waiting patients in arrival order within that department. Staffing is a fixed scenario input, not a scheduling model or a constraint on bed assignment.

The charts show cumulative admissions and discharges from the start, using up to 25 samples (six simulated hours during regular stepping). The 54 and 38 initial in-care patients are baseline occupancy, excluded from new admissions. Active patients include both in-care and waiting patients. Staff cards show eight representative named clinicians; the total staff counts are 24 and 16.

The activity feed retains the latest 40 events; the directory retains active patients and the latest 200 discharged patients after each step. Counters remain cumulative. **Reset simulation** restores only the selected hospital after confirmation. Browser storage is local to the origin; changing port/browser, clearing site data, or using another device gives separate progress. If storage is unavailable or full, the demo continues in memory with a notice.

## API example

Create parents before their dependents. Replace the example IDs below with the IDs returned by your server.

```bash
curl -X POST http://localhost:8080/hospitals \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo Hospital","location":"Boston"}'

curl -X POST http://localhost:8080/roles \
  -H 'Content-Type: application/json' \
  -d '{"name":"Physician","description":"Provides patient care"}'

curl -X POST http://localhost:8080/staff \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Olivia","last_name":"Chen","hospital_id":1,"role_ids":[1]}'

curl -X POST http://localhost:8080/patients \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Alex","last_name":"Taylor","date_of_birth":"1990-05-12","hospital_id":1,"staff_id":1}'
```

All four resources support `POST /resource`, `GET /resource`, `GET /resource/{id}`, `PATCH /resource/{id}`, and `DELETE /resource/{id}`. There is no `/api` prefix. See the [API guide](docs/api/index.md) for payloads, validation, and limitations.

## Relational model

```mermaid
erDiagram
    HOSPITAL ||--o{ STAFF : employs
    HOSPITAL ||--o{ PATIENT : receives
    STAFF o|--o{ PATIENT : treats
    STAFF ||--o{ STAFF_ROLES : has
    ROLE ||--o{ STAFF_ROLES : assigned
    HOSPITAL {
        int id PK
        string name UK
        string location UK
    }
    STAFF {
        int id PK
        string first_name
        string last_name
        int hospital_id FK
    }
    PATIENT {
        int id PK
        string first_name
        string last_name
        date date_of_birth
        int hospital_id FK
        int staff_id FK
    }
    ROLE {
        int id PK
        string name
        string description
    }
    STAFF_ROLES {
        int staff_id PK,FK
        int role_id PK,FK
    }
```

A patient belongs to one hospital and may have one assigned staff member. The patient API checks that assigned staff belongs to the same hospital. Staff can have multiple roles through `staff_roles`. Roles describe occupations; they do not grant access permissions. Hospital names and locations have database uniqueness constraints. Role-name uniqueness is enforced by the router, not a database constraint.

## Repository map

```text
app/                 FastAPI application, database setup, models, CRUD routers
web/src/             React dashboard, CSS, and pure TypeScript simulation engine
web/tests/           Simulation invariants and queue behavior tests
tests/               Isolated API CRUD and relationship regression tests
docs/                English MkDocs guides, API usage, and data model reference
.github/workflows/   Documentation deployment to GitHub Pages
compose.yml          MySQL, API, and frontend services
.env.example         Local configuration template (no production credentials)
run.sh               Non-destructive Compose startup helper
```

## Documentation and checks

```bash
uv sync --locked
uv run mkdocs serve --dev-addr 127.0.0.1:8000
uv run mkdocs build --strict
uv run python -m unittest discover -s tests -v
cd web
npm test
npm run build
```

MkDocs publishes to [https://marcelopenas.github.io/HospitalSim/](https://marcelopenas.github.io/HospitalSim/) through the existing GitHub Actions workflow on pushes to `main`. GitHub Pages must use the `gh-pages` deployment branch. Updating files locally does not publish them.

Simulation tests cover deterministic progression, immutability, patient conservation, department capacity, queue promotion, increased surge demand, and midnight rollover. API regression tests additionally exercise health, Swagger/OpenAPI, full CRUD, and relationship/date validation using an isolated SQLite database. These do not replace MySQL integration tests. See [development](docs/development.md) and [troubleshooting](docs/troubleshooting.md).

## Scope and known limitations

This is an educational project, not clinical software. The API provides storage and CRUD, without authentication, pagination, migrations, or a backend simulation engine. Deleting referenced records, explicitly setting required fields to null in PATCH, and some relationship changes can produce database errors; remove dependents first and provide non-null required fields. Moving a staff member to another hospital does not validate all existing patient assignments. The API health endpoint is a process check, not a database readiness probe. See the API guide before extending the service.

## AI assistance and demonstration

OpenAI ChatGPT/Codex assisted with the dashboard implementation, simulation behavior and tests, English documentation, and development configuration in this revision.

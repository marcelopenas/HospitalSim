# Development

## Repository layout

| Path | Responsibility |
| --- | --- |
| `app/main.py` | FastAPI setup, router registration, startup table creation, health route |
| `app/database.py` | SQLModel engine, environment configuration, per-request session |
| `app/caching.py` | Central HTTP cache policy for successful reads and no-store responses |
| `app/models/` | Table models and request/response schemas |
| `app/routers/` | CRUD and relationship checks |
| `web/src/App.tsx` | Dashboard views, manual forms, request reviews, test controls |
| `web/src/api.ts` | HTTP execution, SQL examples, API response updates |
| `web/src/demo.ts` | Population/test plans, baseline/final state validation |
| `web/src/App.css` / `index.css` | Dashboard layout, styling, and responsive rules |
| `web/tests/` | Node-based API client and workflow tests |
| `tests/` | Schema, ORM, HTTP-cache, and optional MySQL integration tests |
| `docs/` / `mkdocs.yml` | Documentation source and navigation |
| `compose.yml` | API, frontend, and MySQL services |
| `compose.test.yml` / `test.sh` | Isolated MySQL container and complete backend test runner |

## Frontend checks

```bash
cd web
npm ci
npm test
npm run build
```

Tests use Node 24's native TypeScript stripping and built-in test runner. A mock HTTP contract checks repeatable baseline/final values, dynamic server IDs, request JSON, atomic patient-transfer payloads, preservation of unrelated records, prerequisite checks, partial failure/recovery, and null assignment behavior. These are client/workflow tests; they do not execute a real MySQL server or browser interactions. The production build checks TypeScript before bundling. `npm run lint` runs Oxlint.

For UI checks, verify the full-screen empty/populate choices, forms for all four models, request and SQL previews before confirmation, validation errors, keyboard/modal focus, narrow screens, Populate prerequisites, and pause/step/end controls. A failed write must stop the test without retrying. Refreshing must read persisted records without restoring browser fixtures.

The local Vite and Compose Nginx servers proxy `/api` to the backend. Test with the API running; there is no frontend-only simulation mode.

## Python dependencies

```bash
uv sync --locked
```

After an intentional backend dependency change:

```bash
uv lock
uv export --format requirements-txt --no-dev --no-emit-project --output-file requirements.txt
```

Commit `pyproject.toml`, `uv.lock`, and `requirements.txt` together. Docker installs the exported requirements; uv development uses the lockfile. PyMySQL includes its RSA extra for MySQL password authentication. The declared Python version is 3.14+.

## Backend validation

To run the complete backend suite against a fresh MySQL 8.4 container, install Docker Engine/Desktop and Compose v2, start Docker, then run from the repository root:

```bash
bash test.sh
```

The runner builds the existing API Dockerfile, mounts the tests read-only, waits for MySQL's health check, and executes unittest discovery with `TEST_DATABASE_URL` set to `hospitalsim_test`. No host Python, uv, or `.env` is required. Each invocation uses a unique Compose project with no published ports and temporary MySQL storage. Its test containers and network are removed on completion, failure, or interruption; all test data is discarded. The application stack and its `db-data` volume are separate. Docker retains reusable images and build cache. The command returns the test process's exit status; setup or cleanup failures also return a nonzero status.

For local checks without a database:

```bash
uv sync --locked
uv run python -m unittest discover -s tests -v
```

The database integration tests are skipped when `TEST_DATABASE_URL` is unset. To use an existing disposable MySQL instance instead of the container runner, follow the setup below.

Start an accessible MySQL database, export `DATABASE_URL`, and run the service. Use Swagger to exercise create/list/read/patch/delete for all four resources, including missing IDs, duplicate names, invalid dates, invalid references, and same-hospital staff assignment. Verify records persist across a service restart. Create an empty, disposable MySQL schema such as `hospitalsim_test`, with a user permitted to create and drop its tables. Run the API integration suite with:

```bash
export TEST_DATABASE_URL='mysql+pymysql://TEST_USER:TEST_PASSWORD@localhost:3306/hospitalsim_test'
uv run python -m unittest discover -s tests -v
```

These tests use MySQL only. They require an explicit `TEST_DATABASE_URL` using `mysql+pymysql` and a database name ending in `_test`; no application database is used as a fallback. **The suite drops and recreates its test tables, so the named schema must be disposable.** Without that variable, integration tests are skipped. They cover CRUD, references, invalid dates, null PATCH validation, protected deletions, staff transfers, shared-role persistence, and initialization across API clients. The independent ORM regression test runs without MySQL and verifies the role relationship is a collection: adding Mia must preserve Olivia's Physician assignment. The production lifespan is skipped so all table creation is controlled by the suite.

Required PATCH fields reject null with 422; protected deletions and transfers return 409. Commit-time integrity conflicts roll back. `create_all` is not a migration mechanism. Existing databases need the upgrade below, plus `ALTER TABLE role ADD UNIQUE (name);` if the earlier role-name constraint is missing. A deliberate reset with `run.sh` also creates the complete schema, deleting all existing project data.

## Linters

```bash
uv tool run ruff check .
uv tool run ty check --python .venv/bin/python .
```

Run `uv sync --locked` first to create the project environment. Ruff and ty are development tools. The optional [media tools](vid/recording.md) use Pillow and FFmpeg; live UI recording also needs Playwright. Their commands install tools on demand without adding API runtime dependencies.

## Documentation

```bash
uv run mkdocs serve --dev-addr 127.0.0.1:8000
uv run mkdocs build --strict
```

The explicit port avoids conflicting with API development conventions. Markdown sources are English. Navigation is declared in `mkdocs.yml`; add new pages there. Mermaid diagrams are supported through the configured SuperFences extension.

The GitHub Actions workflow builds and publishes on pushes to `main`. Configure GitHub Pages to serve `gh-pages`; the site URL is `https://marcelopenas.github.io/HospitalSim/`. Local edits or a source archive do not publish a documentation update automatically.

## Upgrading an existing schema

New databases receive all columns and constraints through SQLModel. `create_all` does not add columns to an existing table. Stop the API while upgrading an existing database, back it up, and apply the following MySQL 8.4 changes once. MySQL DDL commits implicitly; this is not a transactional migration. If you can discard the data, `bash run.sh` deliberately resets the volumes and recreates the schema instead.

First add nullable columns so existing staff can be backfilled with their real employment details:

```sql
ALTER TABLE hospital ADD COLUMN capacity INT NULL;
UPDATE hospital h
LEFT JOIN (SELECT hospital_id, COUNT(*) AS total FROM patient GROUP BY hospital_id) p
ON p.hospital_id = h.id
SET h.capacity = GREATEST(100, COALESCE(p.total, 0));
ALTER TABLE hospital MODIFY COLUMN capacity INT NOT NULL,
  ADD CONSTRAINT ck_hospital_capacity CHECK (capacity >= 0);

ALTER TABLE role ADD COLUMN access_type CHAR(1) NULL;
UPDATE role SET access_type = 'C';
ALTER TABLE role MODIFY COLUMN access_type CHAR(1) NOT NULL,
  ADD CONSTRAINT ck_role_access_type CHECK (access_type IN ('A', 'B', 'C'));

ALTER TABLE staff
  ADD COLUMN date_of_admission DATE NULL,
  ADD COLUMN last_check_in DATETIME(6) NULL,
  ADD COLUMN salary DECIMAL(12,2) NULL;

ALTER TABLE patient ADD COLUMN image_blob BLOB NULL;
```

The hospital backfill starts at 100 places, increasing it to cover existing patients. Legacy roles start with classification C. Review both values for your data. Set each staff member's real admission date and salary; last check-in may remain null. For example, replace the values and ID below with the actual data:

```sql
UPDATE staff SET date_of_admission = '2024-01-15', salary = 7500.10 WHERE id = 1;
SELECT id FROM staff WHERE date_of_admission IS NULL OR salary IS NULL;
```

The SELECT must return no rows before enforcing NOT NULL. Existing patient images can be backfilled using `FROM_BASE64` and the shipped default icon; print the exact update from the repository root and run it in the chosen MySQL database:

```bash
uv run python - <<'PY'
import base64
from app.images import DEFAULT_IMAGE

encoded = base64.b64encode(DEFAULT_IMAGE).decode("ascii")
print(f"UPDATE patient SET image_blob = FROM_BASE64('{encoded}') WHERE image_blob IS NULL;")
PY
```

Then finish:

```sql
ALTER TABLE staff MODIFY COLUMN date_of_admission DATE NOT NULL,
  MODIFY COLUMN salary DECIMAL(12,2) NOT NULL,
  ADD CONSTRAINT ck_staff_salary CHECK (salary >= 0);
ALTER TABLE patient MODIFY COLUMN image_blob BLOB NOT NULL;
```

Rebuild/restart the API and frontend together. Populate restores fixed values for all the new demo fields and distinct profile icons; it continues to reset patients and staff only in the two reserved demo hospitals.

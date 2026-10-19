# Development

## Repository layout

| Path | Responsibility |
| --- | --- |
| `app/main.py` | FastAPI setup, router registration, startup table creation, health route |
| `app/database.py` | SQLModel engine, environment configuration, per-request session |
| `app/models/` | Table models and request/response schemas |
| `app/routers/` | CRUD and relationship checks |
| `web/src/App.tsx` | Dashboard views, manual forms, request reviews, test controls |
| `web/src/api.ts` | HTTP execution, SQL examples, API response updates |
| `web/src/demo.ts` | Population/test plans, baseline/final state validation |
| `web/src/App.css` / `index.css` | Dashboard layout, styling, and responsive rules |
| `web/tests/` | Node-based API client and workflow tests |
| `tests/` | MySQL-only API integration tests |
| `docs/` / `mkdocs.yml` | Documentation source and navigation |
| `compose.yml` | API, frontend, and MySQL services |

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

Start an accessible MySQL database, export `DATABASE_URL`, and run the service. Use Swagger to exercise create/list/read/patch/delete for all four resources, including missing IDs, duplicate names, invalid dates, invalid references, and same-hospital staff assignment. Verify records persist across a service restart. Create an empty, disposable MySQL schema such as `hospitalsim_test`, with a user permitted to create and drop its tables. Run the API integration suite with:

```bash
export TEST_DATABASE_URL='mysql+pymysql://TEST_USER:TEST_PASSWORD@localhost:3306/hospitalsim_test'
uv run python -m unittest discover -s tests -v
```

These tests use MySQL only. They require an explicit `TEST_DATABASE_URL` using `mysql+pymysql` and a database name ending in `_test`; no application database is used as a fallback. **The suite drops and recreates its test tables, so the named schema must be disposable.** Without that variable, integration tests are skipped. They cover CRUD, references, invalid dates, null PATCH validation, protected deletions, staff transfers, shared-role persistence, and initialization across API clients. The independent ORM regression test runs without MySQL and verifies the role relationship is a collection: adding Mia must preserve Olivia's Physician assignment. The production lifespan is skipped so all table creation is controlled by the suite.

Required PATCH fields reject null with 422; protected deletions and transfers return 409. Commit-time integrity conflicts roll back. `create_all` is not a migration mechanism. Existing databases need `ALTER TABLE role ADD UNIQUE (name);` after resolving duplicate role names, or a deliberate clean reset with `run.sh`.

## Linters

```bash
uv tool run ruff check .
uv tool run ty check --python .venv/bin/python .
```

Run `uv sync --locked` first to create the project environment. Ruff and ty are development tools. The optional archived media renderer requires Pillow (`uv pip install Pillow`) and FFmpeg; no API runtime dependency was added.

## Documentation

```bash
uv run mkdocs serve --dev-addr 127.0.0.1:8000
uv run mkdocs build --strict
```

The explicit port avoids conflicting with API development conventions. Markdown sources are English. Navigation is declared in `mkdocs.yml`; add new pages there. Mermaid diagrams are supported through the configured SuperFences extension.

The GitHub Actions workflow builds and publishes on pushes to `main`. Configure GitHub Pages to serve `gh-pages`; the site URL is `https://marcelopenas.github.io/HospitalSim/`. Local edits or a source archive do not publish a documentation update automatically.

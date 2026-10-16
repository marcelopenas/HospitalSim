# Development

## Repository layout

| Path | Responsibility |
| --- | --- |
| `app/main.py` | FastAPI setup, router registration, startup table creation, health route |
| `app/database.py` | SQLModel engine, environment configuration, per-request session |
| `app/models/` | Table models and request/response schemas |
| `app/routers/` | CRUD and relationship checks |
| `web/src/App.tsx` | Dashboard views, forms, timer, and persistence |
| `web/src/simulation.ts` | Pure seeded simulation engine |
| `web/src/App.css` / `index.css` | Dashboard layout, styling, and responsive rules |
| `web/tests/` | Node-based simulation tests |
| `tests/` | Isolated SQLite API regression tests |
| `docs/` / `mkdocs.yml` | Documentation source and navigation |
| `compose.yml` | API, frontend, and MySQL services |

## Frontend checks

```bash
cd web
npm ci
npm test
npm run build
```

Tests use Node 24's native TypeScript stripping and built-in test runner, without a separate test dependency. They verify repeatability, immutable transitions, capacity limits, conservation of active patients, first-in queue promotion, demand differences, bounded history, and time rollover. The production build checks TypeScript before Vite bundles the app. `npm run lint` is available for Oxlint checks.

For new simulation behavior, prefer pure engine functions and tests for meaningful constraints. For UI work, check keyboard navigation, modal focus, narrow screens, empty search results, waiting queues, state persistence, and unavailable browser storage. These engine tests do not execute browser interactions.

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

Start an accessible MySQL database, export `DATABASE_URL`, and run the service. Use Swagger to exercise create/list/read/patch/delete for all four resources, including missing IDs, duplicate names, invalid dates, invalid references, and same-hospital staff assignment. Verify records persist across a service restart. Run the isolated API regression suite with:

```bash
uv run python -m unittest discover -s tests -v
```

These tests override the database session with in-memory SQLite and skip the production lifespan hook, so they do not create or modify production tables. They cover health, Swagger/OpenAPI, the hospital/role/staff/patient relationship chain, all CRUD methods, duplicate hospitals, cross-hospital assignments, and invalid birth dates. Explicit SQLAlchemy relationship targets avoid deferred type annotations being interpreted as ORM class names on Python 3.14. These checks do not constitute a MySQL integration test suite.

The existing API does not fully guard every null PATCH, deletion, or staff transfer case. Add appropriate integrity validation and transaction handling when extending those paths. `create_all` is not a migration mechanism.

## Documentation

```bash
uv run mkdocs serve --dev-addr 127.0.0.1:8000
uv run mkdocs build --strict
```

The explicit port avoids conflicting with API development conventions. Markdown sources are English. Navigation is declared in `mkdocs.yml`; add new pages there. Mermaid diagrams are supported through the configured SuperFences extension.

The GitHub Actions workflow builds and publishes on pushes to `main`. Configure GitHub Pages to serve `gh-pages`; the site URL is `https://marcelopenas.github.io/HospitalSim/`. Local edits or a source archive do not publish a documentation update automatically.

## Course deliverables

The accompanying SQL brief asks for FastAPI, ORM/MySQL persistence, CRUD for at least two entities, multiple data types, and a well-documented repository. The project implements CRUD for hospitals, staff, roles, and patients. Patient dates, integer IDs, and text fields demonstrate varied types.

Before submission, the owner should verify repository access for the instructors, maintain meaningful commits, record the required API demonstration video, add the video's real URL to the README, and review the AI-assistance disclosure. Those external deliverables cannot be inferred from the source archive.

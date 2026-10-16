# Architecture

HospitalSim has a browser simulation and a separate database-backed API. They share a hospital domain, but they do not synchronize records.

| Component | Technology | Responsibility | Data lifetime |
| --- | --- | --- | --- |
| Dashboard | React, TypeScript, Vite | Views, controls, synthetic scenarios | Browser local storage |
| Simulation engine | Pure TypeScript functions | Seeded arrivals, bed allocation, queues, discharges | Part of dashboard state |
| Static server | Nginx | Serve the built dashboard and SPA fallback | Built files |
| API | FastAPI, SQLModel | Validation and CRUD for four resources | MySQL records |
| Database | MySQL 8.4 in Compose | Relational persistence and foreign keys | Named Docker volume |
| Documentation | MkDocs Material | Guides and data/API reference | Markdown source and GitHub Pages |

## Browser path

`src/App.tsx` manages navigation, forms, an interval timer, and local storage. It calls pure functions in `src/simulation.ts`, which return new state without mutating their input. A seeded generator supplies repeatable fixtures and random arrivals. CSS and inline SVG draw the interface and chart without external image or font services.

The frontend Docker image runs an npm build in a Node 24 stage, then copies `dist/` into Nginx. No Python or database connection is needed to use the dashboard. `VITE_SWAGGER_URL` is embedded at build time and used only as a navigation link.

## API path

Each router receives a SQLModel session through `get_session`, queries or modifies model instances, commits changes, and returns a declared response model. Hospitals, staff, and patients are related through foreign keys; staff and roles are joined through `staff_roles`.

The FastAPI lifespan function calls `SQLModel.metadata.create_all` on startup. The engine is created from the required `DATABASE_URL` environment variable. Compose waits for the database healthcheck before starting the API; `/health` itself reports process health only.

There is no `/api` prefix, authentication, authorization, CORS middleware, pagination, or migration framework. Swagger is supplied by FastAPI at `/docs`. Cross-origin browser API integration would require additional configuration, error handling, and deliberate mapping between the simulation domain and persisted entities.

## Boundaries to preserve when extending

- Keep demo records synthetic and clearly labeled.
- Add explicit migrations rather than relying on `create_all` to alter tables.
- Define transactional admission and discharge behavior before adding backend bed/queue models.
- Enforce cross-hospital assignment rules on all affected update paths, not only patient creation.
- Add authentication and authorization before exposing sensitive records.
- Add MySQL integration tests for referential actions, conflict handling, and concurrency.

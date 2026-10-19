# Architecture

The dashboard, Testing tab, and Swagger all use one FastAPI CRUD API and one MySQL database. The four domain models and join table remain unchanged. One additional infrastructure table, `app_state`, stores the database-wide startup flag.

| Component | Technology | Responsibility |
| --- | --- | --- |
| Dashboard | React, TypeScript, Vite | API-backed views, manual CRUD forms, request/SQL previews |
| Test plans | `web/src/demo.ts` | Fixed fixtures, ordered CRUD operations, baseline/final checks |
| HTTP client | `web/src/api.ts` | HTTP/JSON requests, errors, response updates, illustrative SQL |
| Frontend server | Nginx in Compose; Vite locally | Serve assets and proxy `/api/*` to FastAPI |
| API | FastAPI, SQLModel | Validate requests and execute CRUD transactions |
| Database | MySQL 8.4 | Persist hospitals, roles, staff, patients, and staff-role links |
| Documentation | MkDocs Material | English guides and API/model reference |

## Request path

A dashboard action shows its method, path, JSON, and SQL example before confirmation. The browser sends HTTP to `/api/patients`, for example; the same-origin proxy strips `/api` and forwards `/patients` to FastAPI. Nginx uses Compose's `web:8080`; Vite development/preview use `127.0.0.1:8080`. FastAPI paths retain no `/api` prefix. Swagger's direct default address is port 8080.

Each router obtains a SQLModel session, validates fields and references, modifies model instances, commits, and returns a declared response schema. The dashboard updates from successful responses and reloads collections after manual mutations, population, and completion of a test. There is no polling or synchronization with other clients; use Refresh to read their changes.

**SQL previews are illustrative demo examples, never executable browser input.** The browser sends JSON, not SQL; the backend uses parameterized ORM statements and may execute additional queries. `SQL_ECHO` exposes actual statements in server logs.

## Database-backed startup

`GET /initialization` reads `app_state` row 1, returning `was_initialized=false` when no row exists. The dashboard also loads the four domain collections. If initialized, it opens Overview; otherwise it offers the empty/populated choice. Confirming Start empty or successfully verifying initial population calls `POST /initialization`, which uses a MySQL upsert to save true idempotently. This flag is shared across clients and survives application restarts. GET makes no writes; canceled/failed population does not mark success. A database volume reset clears the flag along with domain data.

## Deterministic orchestration

Populate resets only patients/staff in the two reserved named demo hospitals and restores their hospital/role definitions. Test requires that baseline and sends eight fixed mutations in order. Created IDs are taken from API responses. Resulting domain values and relationships are deterministic; auto-increment IDs may differ.

The test scheduler waits for one response before scheduling another request. Each operation commits independently and remains saved after interruption. Baseline/final checks use API collection reads; a preflight fingerprint catches changes since the confirmation preview. This is not a distributed lock, and other clients must not edit demo records during execution. There is no additional simulation model, server-side scheduler, or separate demo database.

The initialization flag lives in MySQL. The browser stores only loaded API responses, navigation, pending forms, the request log, and the current test cursor in memory. It does not persist domain records in local storage or invent fallback data. Reloading loses the execution cursor but retains MySQL changes.

## Deployment and persistence

The frontend image builds with Node 24 and serves static output in Nginx. `VITE_API_URL` defaults to `/api`; `VITE_SWAGGER_URL` configures the Swagger link. Both are public build-time settings. Static hosting alone cannot run FastAPI/MySQL. A separately hosted frontend needs an accessible API and a reverse proxy or explicit backend CORS configuration.

FastAPI's lifespan creates missing SQLModel tables. `DATABASE_URL` must use `mysql+pymysql`; MySQL is the only supported database. Compose waits for database readiness before API startup. `/health` reports process health, not a database query.

There is no authentication, pagination, or migration framework. `create_all` does not migrate existing tables. The `db-data` volume preserves records across normal restarts; **`run.sh` deliberately removes project volumes** to create a clean empty instance.

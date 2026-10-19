# HospitalSim

A no-login hospital dashboard backed by a FastAPI CRUD API and MySQL. Manage hospitals, roles, staff, and patients manually, or run a fixed sequence of real API operations from the **Testing** tab.

[Documentation](https://marcelopenas.github.io/HospitalSim/) · [Local dashboard](http://localhost:3000) · [Swagger UI](http://localhost:8080/docs)

> [!IMPORTANT]
> **Run the project locally before opening the dashboard or Swagger links.** HospitalSim is intended for local use: manual CRUD operations, population, and testing repeatedly create, modify, and delete database records. A shared public instance would be continually changed and reset, making it unsuitable as a stable demo. The project documentation is available online independently.

![HospitalSim screenshot](docs/assets/dashboard.png)

## Start with Docker

Requires Docker Engine/Desktop and Compose v2.

```bash
cp .env.example .env
# Set local database passwords in .env.
docker compose up --build
```

Open http://localhost:3000. A new database has no domain records. On load, the dashboard checks `GET /initialization` and reads the four collections. The full-screen welcome page offers **Start empty** or **Pre-populate** only until that choice is completed. `POST /initialization` saves the choice in MySQL; refreshes and other browsers then open the dashboard directly. Starting empty preserves existing records. Pre-populate shows the planned writes immediately and marks initialization only after the baseline is verified.

**`bash run.sh` deliberately deletes all project Compose volumes and MySQL records** before rebuilding a clean instance. This reset is intentional for repeatable development and demonstrations. The script exports `requirements.txt` with uv and creates `.env` from the example when missing. `bash run.sh -d` also resets the database. To preserve records, use `docker compose down` and `docker compose up --build` without `-v`.

| Service | Address |
| --- | --- |
| Dashboard | http://localhost:3000 |
| Swagger UI | http://localhost:8080/docs |
| ReDoc | http://localhost:8080/redoc |
| OpenAPI schema | http://localhost:8080/openapi.json |
| Process health | http://localhost:8080/health |

Compose waits for MySQL readiness and creates missing tables on API startup. The MySQL port is internal to Compose; records live in the `db-data` volume. The dashboard's `/api/*` requests are proxied by Nginx to FastAPI, with `/api` stripped. FastAPI itself keeps its original paths, such as `/patients`.

## Manual operations

- **Overview:** patient records, assigned/unassigned patients, staff, hospital counts, and care assignment bars from API responses.
- **Hospitals, Roles, Staff, Patients:** create, list, read individual records, edit, and delete. Create hospitals and roles before dependent staff/patients.
- Choose a hospital or search loaded records without sending extra requests. Sidebar navigation scrolls to the top.
- Use the visible Dark mode switch in the bottom local-profile area. Appearance follows the browser by default; the switch reflects the current theme, and toggling it saves a manual override locally. There is no separate browser-theme button.
- Review the HTTP method, path, JSON payload, and illustrative SQL before sending a request. Successful mutations reload all collections.
- Use **Refresh records** to load changes made through Swagger or other clients. The request log records responses, failures, and SQL previews.

**SQL previews are demo examples only. The browser sends HTTP requests and JSON, never SQL.** The server validates input and uses parameterized ORM queries. The preview approximates checks, statements, and relationship changes; it is not an exact execution log. `SQL_ECHO=true` enables actual backend SQL logging.

## Deterministic Testing

Demo hospitals have capacities of 8 and 4. Staff admission dates, UTC check-ins, decimal salaries, role access codes, and patient images are fixed and verified along with the other fields.

**Populate** restores 2 reserved `[Demo]` hospitals, 3 roles, 3 staff, and 4 patients. It deletes and recreates patients and staff inside those two named hospitals, restores their locations and the three reserved role definitions, and leaves other hospitals and their records intact. Do not put records you want to preserve inside the demo hospitals. The main preview shows the concrete INSERT, UPDATE, DELETE, and join-table writes, with values. Supporting GET requests are grouped separately under preflight and verification reads. The entire reset is previewed before confirmation.

**Test** requires the exact baseline. If it is missing or has changed, a popup explains why and offers to review Populate first. Before execution, the test preview explains the story in plain English, lists the HTTP requests, and shows likely SQL changes. It then opens Overview with controls to pause/resume, advance the next hour, change speed, or end the session.

| Time | Operation |
| --- | --- |
| 08:00 | Admit Avery Stone at Riverside under Olivia Chen |
| 09:00 | Assign Jamie Morgan to Noah Patel |
| 10:00 | Transfer Casey Lee to Riverside and assign Olivia in one PATCH |
| 11:00 | Discharge Sam Rivera by deleting the current patient record |
| 12:00 | Admit Riley Quinn at Lakeside under Mia Brooks |
| 13:00 | Clear Alex Taylor's staff assignment |
| 14:00 | Give Mia the additional shift coordinator role |
| 15:00 | Update Riverside's location to its North campus |

The final demo dataset has **2 hospitals, 3 roles, 3 staff, and 5 patients: 4 assigned, 1 unassigned**. Names, birth dates, operations, and resulting relationships are fixed. MySQL-generated IDs may differ between population runs; IDs are always taken from API responses. Re-run Populate before each new test. These counts exclude unrelated records.

Each request commits independently. One request runs at a time; errors stop execution without automatic retries or rollback of previous steps. Pause allows an in-flight request to finish. Ending a session or reloading the page leaves committed data in MySQL; only the timer/cursor is lost. Initial reads detect changes since the preview, and final reads verify the expected result. Other clients should avoid changing demo records during a run. See the [dashboard guide](docs/dashboard.md).

## Local development

Python 3.14+, uv, Node 24, npm, and an accessible MySQL server are required.

```bash
uv sync --locked
export DATABASE_URL='mysql+pymysql://hospitalsim:YOUR_PASSWORD@localhost:3306/hospitalsim'
uv run fastapi dev app/main.py --port 8080
```

In a second terminal:

```bash
cd web
npm ci
npm run dev
```

Vite normally serves http://localhost:5173 and proxies `/api` to `http://127.0.0.1:8080`. Its preview server uses the same proxy. The frontend requires a running API; there is no local-data fallback. The API reads `DATABASE_URL` from the environment and does not automatically load `.env`. URL-encode special characters in passwords.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Required `mysql+pymysql` connection string for Python |
| `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` | Compose database initialization values |
| `SQL_ECHO` | Enable actual SQL logging; default false |
| `VITE_API_URL` | Public API base URL; default `/api` via same-origin proxy |
| `VITE_SWAGGER_URL` | Swagger navigation URL; default `http://<browser hostname>:8080/docs` |

Frontend variables are embedded **at build time**. Set them in `web/.env.local` for Vite or root `.env` for Compose, then rebuild/restart. They must not contain secrets. Static hosting needs a reachable API: use a same-origin reverse proxy, or configure an HTTPS API URL and explicit CORS permission on that backend. Publishing static assets does not host FastAPI or MySQL.

## API and data model

Four resources support POST/GET collection and GET/PATCH/DELETE item: `/hospitals`, `/roles`, `/staff`, `/patients`. There is no PUT endpoint. Hospital has `name`, `location`, and required `capacity` (maximum patients). Role has `name`, optional `description`, and required `access_type` stored as `CHAR(1)` (`A`, `B`, or `C`); this is classification metadata, not authentication. Staff has names, required `date_of_admission` (`DATE`), optional `last_check_in` (`DATETIME(6)`, UTC), required `salary` (`DECIMAL(12,2)`), `hospital_id`, and `role_ids`. Patient has names, `date_of_birth`, `hospital_id`, optional `staff_id`, and `image_blob` (MySQL `BLOB`, base64 in JSON). Salary uses exact decimal strings such as `"7500.10"`, preserving cents. All have generated integer IDs. Staff and roles use the `staff_roles` join table; a shared role remains assigned to every staff member who has it. A separate one-row `app_state` table stores the database-wide `was_initialized` startup flag, without changing the domain models.

Patients show a default profile in the form and directory; optionally upload a PNG, JPEG, or WebP. Demo profiles have different background colours. The browser prepares small uploads, and the API stores the decoded bytes. Omit an image on PATCH to keep it or use null to restore the default.

A patient and assigned staff member must belong to the same hospital. Admissions/transfers into a full hospital and capacity reductions below its patient count return 409. Referenced deletions and staff transfers with assigned patients return 409. Required PATCH fields reject null with 422; nullable fields can be cleared. Discharge is DELETE, since the model has no admission-status/history field. See the [API guide](docs/api/index.md) and [data model](docs/models/index.md).

`create_all` creates missing tables but does not migrate existing schemas. Existing databases need the new columns and constraints before starting this version; follow [the schema upgrade instructions](docs/development.md#upgrading-an-existing-schema), or deliberately reset with `bash run.sh`. The reset deletes existing data. The service has no authentication, pagination, or migration framework.

## Checks and documentation

```bash
cd web
npm test
npm run lint
npm run build
```

The Node tests use a mock HTTP transport contract to verify deterministic baseline/final states, request payloads, preservation of unrelated records, prerequisites, errors, and null assignments. They do not replace MySQL integration tests or browser interaction checks.

```bash
uv tool run ruff check .
uv tool run ty check --python .venv/bin/python .
uv run mkdocs build --strict
# Use a disposable MySQL schema ending in _test; the suite drops its test tables.
export TEST_DATABASE_URL='mysql+pymysql://TEST_USER:TEST_PASSWORD@localhost:3306/hospitalsim_test'
uv run python -m unittest discover -s tests -v
```

The ORM regression test runs without a server and verifies that assigning a shared role to Mia does not remove it from Olivia. MySQL integration tests also cover capacity limits, date/salary/image round trips, the persisted startup flag, and shared role assignments; they are skipped without `TEST_DATABASE_URL`. The English MkDocs documentation is deployed through the existing GitHub Actions workflow on pushes to `main`. [Showcases](docs/vid/index.md) documents the current UI recording flows. The optional recorder publishes the overview, chapter videos, timestamped JSON, and dashboard image together after a successful capture; current replacement media have not yet been recorded.

## Repository

| Path | Purpose |
| --- | --- |
| `app/` | FastAPI models, CRUD routes, and MySQL session setup |
| `web/src/api.ts` | HTTP execution, SQL examples, response updates |
| `web/src/demo.ts` | Fixed population/test plans and state checks |
| `web/src/App.tsx` | Dashboard, manual forms, previews, testing controls |
| `web/tests/` | API-client and deterministic-workflow tests |
| `tests/` | MySQL integration tests |
| `docs/` | English guides and API/model reference |
| `run.sh` | Deliberate volume reset and clean startup |

## AI assistance

OpenAI ChatGPT/Codex assisted with the dashboard implementation, simulation behavior and tests, English documentation, and development configuration.

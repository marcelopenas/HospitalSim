# Troubleshooting

## The dashboard cannot load records

Start the API and MySQL, then check http://localhost:8080/health and `/hospitals`. The dashboard does not generate browser fixtures when a connection fails. In Compose, Nginx forwards `/api/*` to `web:8080`; Vite development/preview forward to `127.0.0.1:8080`. The prefix is stripped before the API receives the request.

Verify `VITE_API_URL` (default `/api`). Vite variables are embedded at build time; restart Vite or rebuild the frontend after changing them. Static hosting requires a reachable backend and a same-origin proxy or explicit CORS permission on an HTTPS API. The default backend does not enable CORS. A static frontend deployment does not deploy MySQL or FastAPI.

## Swagger does not open

Start the API and check http://localhost:8080/docs. Set `VITE_SWAGGER_URL` for an external API or HTTPS deployment, then rebuild/restart the frontend. The default link uses the current browser hostname and port 8080.

## MySQL connection or authentication fails

Check `docker compose ps` and `docker compose logs web db`. Ensure root `.env` has all four `MYSQL_` variables. Compose uses internal hostname `db`; local Python needs a connection string reachable from the host. The default database container does not publish port 3306.

A MySQL volume retains initialized users and passwords. Editing `.env` alone does not change existing users. Export `DATABASE_URL` for local Python; the app does not load `.env` itself. URL-encode special characters in passwords. Use the locked dependencies, including PyMySQL's RSA extra.

## Test asks to Populate again

Test requires the exact baseline. A completed test, partially completed test, manual edit, extra demo patient/staff, renamed demo hospital, or changed role definition can invalidate it. Review and run Populate to restore the baseline, then confirm the test preview separately. Population resets patients/staff inside the two reserved `[Demo]` hospitals; other hospitals are preserved.

## A preview says the database changed

Initial reads detected changes since the plan was reviewed. No planned mutations are sent in that case. The loaded data has been refreshed: reopen Populate or Test to review the updated plan. Avoid editing demo records from Swagger or another client during a run.

## A test stops or a request times out

Inspect the request log and API logs. Each successful request commits independently. Failures stop execution without retrying or undoing earlier writes. A timeout can occur after a write committed, so refresh and inspect before retrying. Review Populate to restore the known baseline for a new test.

Pause waits for an in-flight request to finish. End session and page reload stop future scheduling but leave committed records in MySQL. The execution cursor is not persisted; it does not resume automatically after a reload.

## API changes do not appear in Overview

Use **Refresh records** and confirm its read preview. The dashboard shows the latest loaded API responses and does not poll other clients. Check the hospital selector and local search filter. All manual dashboard mutations reload collections automatically.

## A request returns 400, 409, 422, or 500

Use IDs returned by the server. Check the `detail` response and relationship prerequisites. Hospital names/locations and role names must be unique. Birth dates must be in the past. Patient and assigned staff must belong to the same hospital. To transfer an assigned patient, update both hospital and staff in one PATCH, or unassign first.

Null required PATCH fields return 422. Referenced-record deletions and staff transfers with assigned patients return 409. Unassign/reassign dependent patients or clear staff-role links before deleting their parents. See the [API guide](api/index.md).

## Preview SQL differs from server logs

This is expected. **SQL previews are demo examples only: the browser sends HTTP/JSON, never SQL.** The server validates requests and executes parameterized ORM statements, including additional relationship/validation reads. The preview is not an exact trace. Set `SQL_ECHO=true` to inspect actual backend statements.

## Startup fails after a schema change

`create_all` creates missing tables but does not alter existing columns or constraints. Apply a database migration for an existing schema. Role-name uniqueness requires the constraint described in [Development](development.md).

## Build versions or ports

Use Node 24 and Python 3.14+. Reinstall with `npm ci` and `uv sync --locked`. Run `npm run build` for TypeScript checks. If port 3000/5173/8080 is occupied, change its configuration. After changing the local backend port, update the Vite proxy target and `VITE_SWAGGER_URL`; rebuild/restart as appropriate. Documentation development uses port 8000.

## Data disappears after run.sh

This is deliberate: `run.sh` exports dependencies, executes `docker compose down -v`, and starts a clean instance. That deletes project volumes and all MySQL records. Use `docker compose down` and `docker compose up --build` without `-v` to preserve data. The next visit offers Start empty or a separately confirmed pre-population.

## Population reports a baseline mismatch

Rebuild both backend and frontend with `docker compose up --build`. An earlier ORM mapping incorrectly inferred a single staff member on the reverse role relationship: assigning the Physician role to Mia removed it from Olivia. The relationship is now explicitly a collection, and the regression test covers that case. Review Populate once to restore the demo baseline. If verification fails again, the message now identifies expected and returned records, including role IDs.

## Welcome appears after refresh

The current version stores the choice in MySQL through `/initialization`, rather than browser memory. Rebuild the backend so this route and the new `app_state` table are available. The welcome remains until Start empty is confirmed or initial population succeeds. A deliberate database reset clears the flag. Deleting domain records alone does not bring back the welcome screen.

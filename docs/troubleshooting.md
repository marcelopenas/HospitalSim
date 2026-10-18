# Troubleshooting

## The dashboard works but Swagger does not open

The dashboard is self-contained; Swagger needs the API. Start the full stack and check http://localhost:8080/health. The default Swagger URL is `http://<browser hostname>:8080/docs`. Set `VITE_SWAGGER_URL` when using an external API or HTTPS, then restart Vite or rebuild the frontend image. Vite variables are build-time values.

## MySQL connection or authentication fails

Check `docker compose ps` and `docker compose logs web db`. Ensure root `.env` exists with all four `MYSQL_` variables. Compose uses the internal hostname `db`, while a local Python process needs a connection string reachable from the host. The default database container does not publish port 3306.

A MySQL volume retains initialized users and passwords. Editing `.env` alone does not change existing database users. Update those users deliberately, or use a separate fresh volume for disposable test data. Do not remove a volume containing data you need.

If Python fails with `KeyError: DATABASE_URL`, export the variable before starting the API. The application does not load `.env` itself. URL-encode special characters in database connection URLs. Use the supplied locked/exported dependencies, including PyMySQL's RSA extra.

## Startup fails after a schema change

`create_all` creates missing tables and does not alter existing columns. Apply an explicit database migration when changing an existing schema. Do not expect a rebuild to migrate or clear the database.

## API records do not appear on the dashboard

This is expected: MySQL-backed CRUD and browser simulation are independent. Use Swagger to inspect API records. The website uses its own synthetic fixtures and browser storage.

## Patients wait even though the hospital has free beds

Beds belong to departments. A patient waiting for an intensive-care bed cannot use an empty surgery bed in this model. Discharge an in-care patient from the same department or advance time. Critical demand can create a sustained queue.

## The clock or chart seems paused

Select **Run simulation**. Reloading the page and switching hospitals pause the timer. An inactive browser tab may throttle timers, and no offline progression is applied. **+1 hour** advances time immediately. The chart begins without generated arrivals and keeps only its latest 25 samples, while counters stay cumulative.

## Progress is missing after reopening the page

Progress is specific to the current origin (scheme, hostname, and port) and browser. Different localhost ports have different storage. Private browsing or clearing site data can remove it. If storage is blocked or full, the dashboard shows a notice and continues without durable persistence.

## A request returns 400, 409, 422, or 500

Use IDs returned by your server rather than assuming the example IDs. Check relationship prerequisites and the `detail` response. Names and locations can conflict; patient birth dates must be in the past; staff assigned to a patient must belong to the same hospital. Null required PATCH fields return 422. Referenced-record deletions and staff transfers with assigned patients return 409. Unassign/reassign dependent patients or remove role links before retrying. Inspect server logs and see the [API guide](api/index.md).

## The build fails on an older Node or Python

Use Node 24 for the dashboard and its native TypeScript tests, and Python 3.14+ for the backend. Reinstall frontend dependencies with `npm ci`, and Python dependencies with `uv sync --locked`. Use `npm run build` to catch TypeScript errors before packaging.

## Port 3000, 5173, or 8080 is already in use

Change the published Compose port or use Vite's `--port` option. If the API port changes, update `VITE_SWAGGER_URL` and rebuild/restart the frontend. For local documentation, use `mkdocs serve --dev-addr 127.0.0.1:8000`.

## Database data disappears after running run.sh

This is deliberate: `run.sh` exports dependencies and executes `docker compose down -v` before starting a clean instance, deleting Compose volumes and all MySQL API records. Use `docker compose down` and `docker compose up --build` without `-v` to preserve data. The browser demo has separate local storage and a separate reset control.

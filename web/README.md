# HospitalSim dashboard

An React/TypeScript dashboard for the FastAPI CRUD API and MySQL. There is no login or browser-local data fallback.

## Run

Start the API on port 8080 with a MySQL connection, then:

```bash
npm ci
npm run dev
```

Vite normally serves http://localhost:5173 and proxies `/api` to `http://127.0.0.1:8080`. `npm run preview` uses the same proxy after `npm run build`. The Compose frontend uses Nginx to forward `/api` to `web:8080`.

On load, GET `/initialization` checks a MySQL flag. The welcome page offers an empty start or reviewed population once per database; POST `/initialization` remembers a completed choice across reloads and browsers. Population previews foreground concrete writes, with supporting reads grouped separately. Overview shows real API counts and care assignments. Hospitals, Roles, Staff, and Patients have manual CRUD forms. Testing has a deterministic Populate baseline and an eight-step Test that commits actual API changes. Test previews explain the operations and expected final state before execution. Its running controls appear on Overview.

Every request has illustrative SQL with the explicit notice that **this is a demo example, the browser sends HTTP and JSON, never SQL**, and actual backend statements may differ. Search/hospital filters send no requests. The request log and test cursor live only for the page session; domain records persist in MySQL.

## Configuration

`VITE_API_URL` defaults to `/api`. `VITE_SWAGGER_URL` defaults to `http://<browser hostname>:8080/docs` (or `<absolute API URL>/docs` when an absolute API base is configured). Set these public build-time values in `web/.env.local` for Vite or root `.env` for Compose and rebuild/restart. Never include credentials. External API hosting requires a same-origin proxy or explicit backend CORS configuration. Static frontend publishing does not host FastAPI or MySQL.

## Files and checks

| File | Responsibility |
| --- | --- |
| `src/api.ts` | Typed request execution, HTTP errors, response updates, SQL examples |
| `src/demo.ts` | Fixed fixtures, population/test plans, baseline/final checks |
| `src/App.tsx` | Startup choices, CRUD forms, previews, dashboard, test scheduling |
| `tests/api-demo.test.ts` | Mock HTTP contract and deterministic workflow checks |

```bash
npm test
npm run lint
npm run build
```

See the [dashboard guide](../docs/dashboard.md) for the baseline, operation schedule, final state, and interruption behavior. The existing data model has no beds, queues, or discharge history; discharge in the test removes the current patient record with DELETE.

# HospitalSim web dashboard

An English, responsive React 19 + TypeScript dashboard built with Vite. It runs a hospital operations simulation entirely in the browser, with no login, database, or external assets required.

## Run and build

Use Node.js 24 and npm:

```bash
npm ci
npm run dev
npm test
npm run build
npm run preview
```

Vite prints the development URL, usually http://localhost:5173. `npm run build` checks TypeScript and produces `dist/`. The provided Dockerfile builds the same output with `npm ci` and serves it through Nginx on port 80 (mapped to port 3000 by root Compose).

## Features

- Overview: current patient and bed counts, staffing, department capacity, patient-flow chart, and activity feed.
- Patients: search, status filters, manual admission, and discharge with automatic queue promotion.
- Staff & roles: representative clinicians, care roles, departments, and current patient assignments.
- Hospitals: two independent, fictional hospital scenarios.
- Simulation: run/pause, 1×/2×/4× speeds, +1 hour, normal/surge/critical demand, and confirmed reset.
- Persistent top links to the project documentation and Swagger.

State is saved under `hospitalsim.demo.v1` in local storage. The simulation starts paused after refresh. If storage fails, the session continues in memory. It does not communicate with the REST API; opening Swagger is the path to database-backed CRUD. Use synthetic patient names only.

## Configuration

Copy `.env.example` to `.env.local` if you need a custom Swagger link:

```dotenv
VITE_SWAGGER_URL=https://your-api.example/docs
```

By default, Swagger opens `http://<current browser hostname>:8080/docs`. This must be reachable from the visitor's browser. The documentation link is `https://marcelopenas.github.io/HospitalSim/`.

Vite embeds `VITE_` variables in public JavaScript at build time. Never put credentials in them. For Docker, set root `.env`'s `VITE_SWAGGER_URL` and rebuild the frontend; setting a runtime Nginx environment variable does not rebuild static files.

## Source map and behavior

| File | Purpose |
| --- | --- |
| `src/App.tsx` | Navigation, dashboard views, forms, timer, and persistence |
| `src/simulation.ts` | Types, seeded fixtures, arrivals, discharges, queues, and history |
| `src/App.css`, `src/index.css` | Responsive layout and visual design |
| `tests/simulation.test.ts` | Node's built-in tests for the pure simulation engine |

New arrivals receive a department, a lead clinician, and a 60–479 minute stay. A 15-minute step completes eligible stays, assigns waiting patients to freed beds, and adds 1–3, 4–6, or 7–9 arrivals according to the scenario. Staff totals are fixed inputs. The chart uses cumulative counters and up to 25 points; up to 40 activity events and 200 discharged records are retained after stepping. See the [simulation guide](../docs/dashboard.md) for exact metrics and constraints.

The UI uses native buttons, labeled inputs, a keyboard-accessible navigation menu, a skip link, live action feedback, and modal dialogs with browser-managed focus. CSS adapts to narrow screens and respects reduced-motion preferences.

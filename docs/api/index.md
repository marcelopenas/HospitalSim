# API usage

The API is available at `http://localhost:8080` in the default Compose setup. There is **no `/api` prefix**. [Swagger UI](http://localhost:8080/docs), [ReDoc](http://localhost:8080/redoc), and the [OpenAPI schema](http://localhost:8080/openapi.json) describe the running service.

Swagger's **Try it out**, the dashboard, and Testing all use these same endpoints and MySQL records. Use **Refresh records** in the dashboard to load changes made through Swagger or another client. The frontend's `/api` URL is a reverse-proxy prefix, stripped before requests reach FastAPI.

## Resources and methods

Replace `{id}` with the integer resource ID. The actual parameter names are `hospital_id`, `patient_id`, `staff_id`, and `role_id`.

| Resource | Collection | Item | Methods |
| --- | --- | --- | --- |
| Hospitals | `/hospitals` | `/hospitals/{id}` | POST, GET collection; GET, PATCH, DELETE item |
| Roles | `/roles` | `/roles/{id}` | POST, GET collection; GET, PATCH, DELETE item |
| Staff | `/staff` | `/staff/{id}` | POST, GET collection; GET, PATCH, DELETE item |
| Patients | `/patients` | `/patients/{id}` | POST, GET collection; GET, PATCH, DELETE item |

All create/update payloads are JSON. Successful creates return the new record with status 201; list/read/update responses use 200; deletes use 204 with no body. PATCH applies supplied fields, rather than replacing the record. Lists return JSON arrays without pagination, search, filters, or an ordering guarantee. There is no PUT endpoint.

## HTTP cache policy

Successful collection/item GET responses use these browser-cache lifetimes:

| Resource | Cache-Control | Lifetime |
| --- | --- | --- |
| Roles | `private, max-age=300, must-revalidate` | 5 minutes |
| Hospitals | `private, max-age=60, must-revalidate` | 1 minute |
| Staff | `private, max-age=15, must-revalidate` | 15 seconds |
| Patients, including image data | `no-store` | Never store |

Write responses (POST/PATCH/DELETE), initialization, health, unlisted routes, redirects, and handled HTTP errors use `no-store`. The policy is centralized in `app/caching.py` and registered once in `app/main.py`; endpoint functions do not repeat header assignments. Item policies match resolved route templates, including dynamic IDs and requests with query strings.

`private` permits browser storage and excludes shared proxy/CDN caches. `must-revalidate` prevents reuse after the lifetime expires without successful server validation; the API currently returns fresh responses rather than implementing ETags or 304 handling. These headers do not add a server-side result cache: requests reaching FastAPI still execute normal database operations. Other clients can see cached roles/hospitals/staff until their lifetime expires; updating an item does not automatically invalidate every related collection cached by other clients.

The dashboard deliberately uses Fetch `cache: 'no-store'` for every GET, including initial reads, individual reads, post-write refreshes, Populate/Test preflight checks, and final verification. Those actions always reach the backend and do not store patient data or reuse stale browser responses. Clients outside the dashboard can use the lifetimes above. The dashboard's loaded in-memory view and request log remain visible for the current page session; HTTP cache prevention does not erase an already displayed record.

## Create a complete relationship chain

Create a hospital and role, then staff, then a patient. Example IDs assume a fresh database; always use IDs actually returned by your API.

### 1. Hospital

```bash
curl -X POST http://localhost:8080/hospitals \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo Hospital","location":"Boston","capacity":100}'
```

```json
{"id":1,"name":"Demo Hospital","location":"Boston","capacity":100}
```

### 2. Role

```bash
curl -X POST http://localhost:8080/roles \
  -H 'Content-Type: application/json' \
  -d '{"name":"Physician","description":"Provides patient care","access_type":"A"}'
```

```json
{"id":1,"name":"Physician","description":"Provides patient care","access_type":"A"}
```

### 3. Staff

```bash
curl -X POST http://localhost:8080/staff \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Olivia","last_name":"Chen","hospital_id":1,"role_ids":[1],"date_of_admission":"2024-01-15","last_check_in":"2026-01-12T08:30:00","salary":"7500.10"}'
```

```json
{"id":1,"first_name":"Olivia","last_name":"Chen","hospital_id":1,"role_ids":[1],"date_of_admission":"2024-01-15","last_check_in":"2026-01-12T08:30:00","salary":"7500.10"}
```

### 4. Patient

```bash
curl -X POST http://localhost:8080/patients \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Alex","last_name":"Taylor","date_of_birth":"1990-05-12","hospital_id":1,"staff_id":1}'
```

```json
{"id":1,"first_name":"Alex","last_name":"Taylor","date_of_birth":"1990-05-12","hospital_id":1,"staff_id":1}
```

Patient responses also include `image_blob` as base64; it is omitted from the short example above. The API supplies the default icon when the create request omits it. For custom images and reset semantics, see [Patient profile images](../models/patient.md#profile-images).

`staff_id` may be omitted or set to null at patient creation. When supplied, it must identify staff at the patient's hospital. `date_of_birth` is an ISO date strictly before today's UTC date.

## Read, update, and delete

```bash
curl http://localhost:8080/patients
curl http://localhost:8080/patients/1

curl -X PATCH http://localhost:8080/patients/1 \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Alexandra","staff_id":null}'

curl -X PATCH http://localhost:8080/staff/1 \
  -H 'Content-Type: application/json' \
  -d '{"role_ids":[]}'

curl -i -X DELETE http://localhost:8080/patients/1
```

`staff_id: null` explicitly unassigns a patient; omitting it leaves the assignment unchanged. For staff PATCH, `role_ids: []` removes all roles, omission or null leaves existing roles unchanged, and a list replaces the set of roles. Duplicate input role IDs collapse to unique relationships.

Delete dependents first: patients, then staff, then hospitals; remove staff-role links by updating/deleting staff before deleting roles. A referenced hospital, staff member with assigned patients, or assigned role returns 409 on deletion without changing those records. Unreferenced staff deletion removes its role links but retains roles. Integrity conflicts during commit roll back and return 409.

## Validation and errors

| Status | Typical meaning |
| --- | --- |
| 400 | Missing referenced hospital/staff/role; patient and clinician belong to different hospitals |
| 404 | Requested item ID not found |
| 409 | Duplicate hospital name/location or role name; protected deletion/staff transfer; full hospital or capacity below patient count |
| 422 | Invalid request schema, null required PATCH field, non-positive path ID, empty/overlong string, missing field, or non-past birth date |
| 500 | Unhandled server/database error; check logs |

Router errors use an envelope such as:

```json
{"detail":"staff_id and hospital_id must refer to the same hospital"}
```

FastAPI's 422 response has a structured `detail` array describing field validation errors. Check the actual response body instead of relying on status alone.

## Current limitations

There is no authentication, pagination, or server-side list filtering. Testing orchestrates a fixed sequence of CRUD requests from the dashboard; the resulting domain records persist in MySQL, while the timer and execution cursor last only for the current page session. Hospital and role uniqueness are enforced by the router and database for new tables. Required PATCH fields may be omitted but reject explicit null with 422. Patient `staff_id`, staff `last_check_in`, and role `description` can be cleared with null; patient `image_blob: null` restores the default profile; null staff `role_ids` leaves roles unchanged. Every staff update validates its resulting hospital (400 if missing), including when roles are omitted. A transfer with assigned patients returns 409; unassign/reassign them before moving staff. Existing schemas require the columns and constraints in [Upgrading an existing schema](../development.md#upgrading-an-existing-schema).

## Health endpoint

```bash
curl http://localhost:8080/health
```

```json
{"status":"ok"}
```

This confirms the process responds; it does not execute a database readiness query.

## Dashboard SQL previews

Every dashboard request has an illustrative SQL preview. **This is a demo example: the browser sends HTTP and JSON, never SQL.** The backend validates requests and executes parameterized SQLModel/SQLAlchemy queries. Previews show likely checks, writes, and relationship changes, rather than exact SQL text or execution order. Enable `SQL_ECHO=true` and inspect API logs to see actual statements.

## Dashboard initialization

| Endpoint | Behavior |
| --- | --- |
| GET `/initialization` | Read the MySQL startup flag; no row means false; does not mutate data |
| POST `/initialization` | Idempotently set the flag true with a MySQL upsert; no request body |

Both return `{"was_initialized": true}` or false as appropriate. This metadata is separate from the four CRUD resources. The dashboard checks it automatically on load, saving true after the empty startup choice or successful population. The flag survives restarts and is shared between browsers; only a database reset clears it. These routes do not populate or delete domain records.

## Exact field types

`capacity` is a required non-negative integer. The API locks the hospital while counting patients; a full hospital cannot accept another patient. `date_of_admission` is required `YYYY-MM-DD`, and `last_check_in` is an optional ISO date/time stored in UTC as DATETIME(6). `salary` is required and limited to DECIMAL(12,2), including a maximum of 9999999999.99 and at most two fractional digits. Prefer a JSON string to avoid floating-point rounding; the response uses exactly two fractional digits. Role `access_type` is required and must be A, B, or C. Patient `image_blob` is optional base64 JSON for PNG/JPEG/WebP, limited to 65535 decoded bytes. Swagger includes these schemas and descriptions.

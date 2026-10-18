# API usage

The API is available at `http://localhost:8080` in the default Compose setup. There is **no `/api` prefix**. [Swagger UI](http://localhost:8080/docs), [ReDoc](http://localhost:8080/redoc), and the [OpenAPI schema](http://localhost:8080/openapi.json) describe the running service.

Swagger's **Try it out** sends real requests and changes MySQL records. It does not change the browser simulation.

## Resources and methods

Replace `{id}` with the integer resource ID. The actual parameter names are `hospital_id`, `patient_id`, `staff_id`, and `role_id`.

| Resource | Collection | Item | Methods |
| --- | --- | --- | --- |
| Hospitals | `/hospitals` | `/hospitals/{id}` | POST, GET collection; GET, PATCH, DELETE item |
| Roles | `/roles` | `/roles/{id}` | POST, GET collection; GET, PATCH, DELETE item |
| Staff | `/staff` | `/staff/{id}` | POST, GET collection; GET, PATCH, DELETE item |
| Patients | `/patients` | `/patients/{id}` | POST, GET collection; GET, PATCH, DELETE item |

All create/update payloads are JSON. Successful creates return the new record with status 201; list/read/update responses use 200; deletes use 204 with no body. PATCH applies supplied fields, rather than replacing the record. Lists return JSON arrays without pagination, search, filters, or an ordering guarantee. There is no PUT endpoint.

## Create a complete relationship chain

Create a hospital and role, then staff, then a patient. Example IDs assume a fresh database; always use IDs actually returned by your API.

### 1. Hospital

```bash
curl -X POST http://localhost:8080/hospitals \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo Hospital","location":"Boston"}'
```

```json
{"id":1,"name":"Demo Hospital","location":"Boston"}
```

### 2. Role

```bash
curl -X POST http://localhost:8080/roles \
  -H 'Content-Type: application/json' \
  -d '{"name":"Physician","description":"Provides patient care"}'
```

```json
{"id":1,"name":"Physician","description":"Provides patient care"}
```

### 3. Staff

```bash
curl -X POST http://localhost:8080/staff \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Olivia","last_name":"Chen","hospital_id":1,"role_ids":[1]}'
```

```json
{"id":1,"first_name":"Olivia","last_name":"Chen","hospital_id":1,"role_ids":[1]}
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
| 409 | Duplicate hospital name/location or role name; protected deletion or staff transfer |
| 422 | Invalid request schema, null required PATCH field, non-positive path ID, empty/overlong string, missing field, or non-past birth date |
| 500 | Unhandled server/database error; check logs |

Router errors use an envelope such as:

```json
{"detail":"staff_id and hospital_id must refer to the same hospital"}
```

FastAPI's 422 response has a structured `detail` array describing field validation errors. Check the actual response body instead of relying on status alone.

## Current limitations

There is no authentication, pagination, filtering, or backend simulation state. Hospital and role uniqueness are enforced by the router and database for new tables. Required PATCH fields may be omitted but reject explicit null with 422. Only patient `staff_id` and role `description` can be cleared with null; null staff `role_ids` leaves roles unchanged. Every staff update validates its resulting hospital (400 if missing), including when roles are omitted. A transfer with assigned patients returns 409; unassign/reassign them before moving staff. Existing schemas require the role-name constraint described in the development guide.

## Health endpoint

```bash
curl http://localhost:8080/health
```

```json
{"status":"ok"}
```

This confirms the process responds; it does not execute a database readiness query.

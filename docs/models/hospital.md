# Hospital

A hospital is the parent facility for staff and patients. Defined in `app/models/hospital.py`; managed through `/hospitals`.

| Field | Type | Required on create | Validation |
| --- | --- | --- | --- |
| `id` | integer | Generated | Primary key, read-only in API payloads |
| `name` | string | Yes | 1–200 characters; unique |
| `location` | string | Yes | 1–500 characters; unique |
| `capacity` | integer (MySQL INT) | Yes | 0–2147483647; maximum patient count |

Location is free text; it is not parsed or verified as a postal address. Name and location each have separate database uniqueness constraints and router-level conflict checks.

## Relationships

A hospital has many staff and patients. Each of those records references one hospital through `hospital_id`. Hospital responses contain only `id`, `name`, `location`, and `capacity`, without embedded relationship arrays.

## Example

```json
{"name":"Riverside Medical Center","location":"Boston, Massachusetts","capacity":100}
```

PATCH may supply name, location, or capacity. The API returns 409 for admissions/transfers into a full hospital or for lowering capacity below its current patient count. Zero capacity blocks admissions. Patient writes and capacity updates lock the hospital row while checking the count, so concurrent admissions cannot claim the same final slot. Omit unchanged fields and do not set required values to null. A missing item returns 404 and a detected duplicate returns 409. Deleting a hospital with staff or patients returns 409. Remove or move those dependents first. Explicit null in a required PATCH field returns 422.

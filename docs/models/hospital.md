# Hospital

A hospital is the parent facility for staff and patients. Defined in `app/models/hospital.py`; managed through `/hospitals`.

| Field | Type | Required on create | Validation |
| --- | --- | --- | --- |
| `id` | integer | Generated | Primary key, read-only in API payloads |
| `name` | string | Yes | 1–200 characters; unique |
| `location` | string | Yes | 1–500 characters; unique |

Location is free text; it is not parsed or verified as a postal address. Name and location each have separate database uniqueness constraints and router-level conflict checks.

## Relationships

A hospital has many staff and patients. Each of those records references one hospital through `hospital_id`. Hospital responses contain only `id`, `name`, and `location`, without embedded relationship arrays.

## Example

```json
{"name":"Riverside Medical Center","location":"Boston, Massachusetts"}
```

PATCH may supply either name or location. Omit unchanged fields and do not set required values to null. A missing item returns 404 and a detected duplicate returns 409. Remove dependent staff and patients before deleting a hospital; deletion behavior is not normalized into a complete API-level integrity-error contract.

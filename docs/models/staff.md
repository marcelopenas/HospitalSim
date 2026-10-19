# Staff

A staff member belongs to a hospital, can have multiple roles, and can be assigned patients. Defined in `app/models/staff.py`; managed through `/staff`.

| Field | Type | Required on create | Validation |
| --- | --- | --- | --- |
| `id` | integer | Generated | Primary key |
| `first_name` | string | Yes | 1–100 characters |
| `last_name` | string | Yes | 1–100 characters |
| `date_of_admission` | MySQL DATE | Yes | `YYYY-MM-DD`, with no time component |
| `last_check_in` | MySQL DATETIME(6) or null | No | UTC date and time; null means no recorded check-in |
| `salary` | MySQL DECIMAL(12,2) / NUMERIC(12,2) | Yes | 0–9999999999.99; at most 2 decimal places |
| `hospital_id` | integer | Yes | Existing hospital checked on create and update |
| `role_ids` | integer array | No | Defaults to `[]`; referenced roles must exist |

`role_ids` is a create/update/read schema field, not a column in `staff`. The ORM stores relationships through `staff_roles`. Read responses return sorted role IDs. There is no singular `role` field.

## Example

```json
{
  "first_name":"Olivia",
  "last_name":"Chen",
  "date_of_admission":"2024-01-15",
  "last_check_in":"2026-01-12T08:30:00",
  "salary":"7500.10",
  "hospital_id":1,
  "role_ids":[1,2]
}
```

Salary is an exact decimal amount, not a floating-point column. Send a JSON decimal string (for example `"7500.10"`); responses always return a string with two decimal places. Currency and pay period are not prescribed. Invalid precision, negative amounts, and amounts exceeding the column range return 422.

Check-in inputs without an offset are interpreted as UTC. Offset-aware inputs are converted to UTC before storage; read responses omit the offset. Microseconds are retained by DATETIME(6). The dashboard labels the date/time input as UTC. PATCH with `last_check_in: null` clears it, while omission retains it. Admission date and salary are required and reject null.

## Role updates

PATCH with `role_ids: [1,2]` replaces current roles. `role_ids: []` clears them. Omitting the field or setting it to null leaves roles unchanged. Duplicate IDs are deduplicated through the relationship query. Invalid role references return 400.

## Relationship limitations

The resulting hospital is validated on every update, even without role changes. Transfers to a different hospital and deletions return 409 while patients remain assigned. Unassign/reassign patients first. Required fields reject explicit null with 422; a failed validation leaves staff fields and roles unchanged.

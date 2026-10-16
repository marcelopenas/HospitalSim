# Patient

A patient belongs to one hospital and can optionally be assigned a staff member. Defined in `app/models/patient.py`; managed through `/patients`.

| Field | Type | Required on create | Validation |
| --- | --- | --- | --- |
| `id` | integer | Generated | Primary key |
| `first_name` | string | Yes | 1–100 characters |
| `last_name` | string | Yes | 1–100 characters |
| `date_of_birth` | ISO date | Yes | Strictly before the current UTC date |
| `hospital_id` | integer | Yes | Must identify an existing hospital |
| `staff_id` | integer or null | No | If present, existing staff in the same hospital |

## Example

```json
{
  "first_name":"Alex",
  "last_name":"Taylor",
  "date_of_birth":"1990-05-12",
  "hospital_id":1,
  "staff_id":1
}
```

The read schema returns these fields plus the generated `id`. It does not include medical history, diagnosis, beds, departments, admission status, or treatment records.

## Updates and relationships

Omit `staff_id` in PATCH to retain the current assignment; set it to null to unassign. When moving a patient, update `hospital_id` and provide compatible `staff_id` in the same request, or unassign the staff member. The router checks the resulting patient/hospital/staff combination on create and update.

A nonexistent referenced hospital or staff member, or a cross-hospital assignment, returns 400. A missing patient returns 404; an invalid birth date returns 422. Required fields should never be explicitly set to null in PATCH.

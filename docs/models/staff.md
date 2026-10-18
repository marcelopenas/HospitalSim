# Staff

A staff member belongs to a hospital, can have multiple roles, and can be assigned patients. Defined in `app/models/staff.py`; managed through `/staff`.

| Field | Type | Required on create | Validation |
| --- | --- | --- | --- |
| `id` | integer | Generated | Primary key |
| `first_name` | string | Yes | 1–100 characters |
| `last_name` | string | Yes | 1–100 characters |
| `hospital_id` | integer | Yes | Existing hospital checked on create and update |
| `role_ids` | integer array | No | Defaults to `[]`; referenced roles must exist |

`role_ids` is a create/update/read schema field, not a column in `staff`. The ORM stores relationships through `staff_roles`. Read responses return sorted role IDs. There is no singular `role` field.

## Example

```json
{
  "first_name":"Olivia",
  "last_name":"Chen",
  "hospital_id":1,
  "role_ids":[1,2]
}
```

## Role updates

PATCH with `role_ids: [1,2]` replaces current roles. `role_ids: []` clears them. Omitting the field or setting it to null leaves roles unchanged. Duplicate IDs are deduplicated through the relationship query. Invalid role references return 400.

## Relationship limitations

The resulting hospital is validated on every update, even without role changes. Transfers to a different hospital and deletions return 409 while patients remain assigned. Unassign/reassign patients first. Required fields reject explicit null with 422; a failed validation leaves staff fields and roles unchanged.

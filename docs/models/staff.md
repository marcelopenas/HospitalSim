# Staff

A staff member belongs to a hospital, can have multiple roles, and can be assigned patients. Defined in `app/models/staff.py`; managed through `/staff`.

| Field | Type | Required on create | Validation |
| --- | --- | --- | --- |
| `id` | integer | Generated | Primary key |
| `first_name` | string | Yes | 1–100 characters |
| `last_name` | string | Yes | 1–100 characters |
| `hospital_id` | integer | Yes | Existing hospital checked on create |
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

Creating a staff member validates its hospital. Updating a hospital without also updating roles does not use the same reference-validation helper, and moving staff does not revalidate assigned patients. Keep patient assignments consistent before moves. Delete dependent patients before staff, or explicitly unassign patients through patient PATCH. Required staff fields must remain non-null.

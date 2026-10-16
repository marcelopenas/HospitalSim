# Role

Roles describe staff occupations or responsibilities. They do not grant authentication or access-control permissions. Defined in `app/models/role.py`; managed through `/roles`.

| Field | Type | Required on create | Validation |
| --- | --- | --- | --- |
| `id` | integer | Generated | Primary key |
| `name` | string | Yes | 1–100 characters |
| `description` | string or null | No | At most 500 characters |

## Example

```json
{"name":"Physician","description":"Provides clinical care"}
```

The router rejects duplicate names with 409 when creating or renaming roles. There is no database unique constraint on `role.name`, so this check alone is not concurrency-safe. Missing role IDs return 404.

## Staff relationships

Staff and roles have a many-to-many relationship through `StaffRoleLink`, stored in `staff_roles` with composite primary key `(staff_id, role_id)`. Assign and remove roles through a staff member's `role_ids` field. Clear related assignments before deleting a role. Role PATCH permits `description: null` to clear the optional description; keep `name` non-null.

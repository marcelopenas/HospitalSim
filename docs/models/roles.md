# Role

Roles describe staff occupations or responsibilities and carry a one-character hospital access classification. The classification is metadata; the API remains unauthenticated and does not enforce these codes as permissions. Defined in `app/models/role.py`; managed through `/roles`.

| Field | Type | Required on create | Validation |
| --- | --- | --- | --- |
| `id` | integer | Generated | Primary key |
| `name` | string | Yes | 1–100 characters |
| `description` | string or null | No | At most 500 characters |
| `access_type` | MySQL CHAR(1) | Yes | Exactly `A`, `B`, or `C` |

## Example

```json
{"name":"Physician","description":"Provides clinical care","access_type":"A"}
```

The router rejects duplicate names with 409 when creating or renaming roles. New tables also enforce role-name uniqueness in MySQL. Existing tables need the unique constraint described in the development guide. Missing role IDs return 404.

## Staff relationships

Staff and roles have a many-to-many relationship through `StaffRoleLink`, stored in `staff_roles` with composite primary key `(staff_id, role_id)`. Assign and remove roles through a staff member's `role_ids` field. An assigned role returns 409 on deletion; clear related assignments first. Role PATCH permits `description: null` to clear the optional description; keep `name` and `access_type` non-null. An access code outside A/B/C returns 422. The database also checks the allowed codes.

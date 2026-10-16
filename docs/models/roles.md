# Roles

The Roles model defines the different roles that users can have within the healthcare system. Each role has specific permissions and responsibilities associated with it.

## Attributes

| Attribute   | Type    | Description                     |
| ----------- | ------- | ------------------------------- |
| id          | Integer | Unique identifier for the role  |
| name        | String  | The name of the role            |
| description | String  | A brief description of the role |

## Relationships

- The Roles model has a many-to-many relationship with the Staff model, where each staff member can have multiple roles, and each role can be assigned to multiple staff members.

## Restrictions

- The `name` attribute is required and must be unique across all roles in the system.
- The `description` attribute is optional but can provide additional context about the role's responsibilities.
- The `id` attribute is automatically generated and cannot be modified.

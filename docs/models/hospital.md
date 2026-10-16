# Hospital

The Hospital model represents a healthcare facility where patients receive medical care. It contains information about the hospital's name, location, departments, and other relevant details necessary for managing hospital operations.

## Attributes

| Attribute | Type    | Description                          |
| --------- | ------- | ------------------------------------ |
| id        | Integer | Unique identifier for the hospital   |
| name      | String  | The name of the hospital             |
| location  | String  | The physical address of the hospital |

## Relationships

The Hospital model has the following relationships:

- The Hospital model has a one-to-many relationship with the Staff model, where each hospital can have multiple staff members.
- The Hospital model has a one-to-many relationship with the Patient model, where each hospital can have multiple patients.

## Restrictions

The Hospital model has the following restrictions:

- The `name` attribute is required and must be unique across all hospitals in the system.
- The `location` attribute is required and must be a valid address and unique across all hospitals in the system.
- The `id` attribute is automatically generated and cannot be modified.

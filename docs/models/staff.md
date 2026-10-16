# Staff

The Staff model represents a staff member in the healthcare system. It contains personal information, professional details, and other relevant attributes necessary for managing staff operations.

## Attributes

| Attribute   | Type    | Description                                                  |
| ----------- | ------- | ------------------------------------------------------------ |
| id          | Integer | Unique identifier for the staff member                       |
| first_name  | String  | The staff member's first name                                |
| last_name   | String  | The staff member's last name                                 |
| role        | Integer | The staff member's role (e.g., doctor, nurse, administrator) |
| hospital_id | Integer | The ID of the hospital where the staff member is employed    |

## Relationships

The Staff model has the following relationships:

- The Staff model has a many-to-one relationship with the Hospital model, where each staff member is associated with a specific hospital.
- The Staff model has a many-to-many relationship with the Roles model, where each staff member can have multiple roles, and each role can be assigned to multiple staff members.
- The Staff model has a one-to-many relationship with the Patient model, where each staff member can be assigned to multiple patients.

## Restrictions

The Staff model has the following restrictions:

- The `first_name` and `last_name` attributes are required.
- The `role` attribute must reference a valid role in the system.
- The `hospital_id` attribute must reference a valid hospital in the system.
- The `id` attribute is automatically generated and cannot be modified.

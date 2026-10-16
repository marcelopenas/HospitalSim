# Patient

The Patient model represents a patient in the healthcare system. It contains personal information, medical history, and other relevant details necessary for managing patient care.

## Attributes

| Attribute     | Type    | Description                                         |
| ------------- | ------- | --------------------------------------------------- |
| id            | Integer | Unique identifier for the patient                   |
| first_name    | String  | The patient's first name                            |
| last_name     | String  | The patient's last name                             |
| date_of_birth | Date    | The patient's date of birth                         |
| staff_id      | Integer | The ID of the staff member assigned to the patient  |
| hospital_id   | Integer | The ID of the hospital where the patient is treated |

## Relationships

- The Patient model has a many-to-one relationship with the Staff model, where each patient is assigned to a specific staff member.
- The Patient model has a many-to-one relationship with the Hospital model, where each patient is associated with a specific hospital.

## Restrictions

The Patient model has the following restrictions:

- The `first_name` and `last_name` attributes are required.
- The `date_of_birth` attribute must be a valid date in the past.
- The `staff_id` attribute must reference a valid staff member in the system.
- The `hospital_id` attribute must reference a valid hospital in the system.
- The `id` attribute is automatically generated and cannot be modified.
- If `staff_id` is provided, the `hospital_id` must also be provided and be the same hospital.

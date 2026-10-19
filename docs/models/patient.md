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
| `image_blob` | MySQL BLOB; base64 string in JSON | No | PNG, JPEG, or WebP, up to 65535 decoded bytes; default profile icon if omitted/null |

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

The read schema returns these fields plus the generated `id`, including `image_blob` as a base64 string. The example above omits the optional image; the API response additionally contains the generated default profile bytes. It does not include medical history, diagnosis, beds, departments, admission status, or treatment records.

## Profile images

The Patients form shows the default profile immediately. **Upload custom image** is optional: choose PNG, JPEG, or WebP up to 5 MB. The browser centre-crops and prepares a 256 × 256 JPEG, then sends base64 through the normal JSON POST/PATCH confirmation. The API validates base64, size, and supported image headers, decodes it, and stores binary bytes in a BLOB. Direct API clients must send at most 65535 decoded bytes, without a `data:image/...;base64,` prefix.

Omit `image_blob` in PATCH to keep it; null restores the default icon. **Use default profile** resets the form preview. Demo patients share the same generic silhouette with distinct coloured backgrounds, including the two patients admitted by Test. Images appear in both the directory and Overview patient registry.

## Updates and relationships

Omit `staff_id` in PATCH to retain the current assignment; set it to null to unassign. When moving a patient, update `hospital_id` and provide compatible `staff_id` in the same request, or unassign the staff member. The router checks the resulting patient/hospital/staff combination on create and update.

A nonexistent referenced hospital or staff member, or a cross-hospital assignment, returns 400. A missing patient returns 404; an invalid birth date or image returns 422. Admission or transfer into a hospital at capacity returns 409, without moving or creating the patient. Editing a patient already at that hospital does not consume another place. Required fields should never be explicitly set to null in PATCH.

"""ORM relationship regressions that do not require a database server."""

import unittest

from sqlalchemy.orm import class_mapper, configure_mappers

from app.models.role import Role
from app.models.staff import Staff, StaffCreate


class RoleRelationshipTests(unittest.TestCase):
    def test_assigning_a_shared_role_does_not_remove_existing_assignments(self):
        configure_mappers()
        physician = Role(id=1, name="Physician")
        staff = []
        for name in ("Olivia", "Mia"):
            person = Staff.model_validate(
                StaffCreate(first_name=name, last_name="Example", hospital_id=1, role_ids=[1]),
                update={"roles": [physician]},
            )
            staff.append(person)
        self.assertTrue(class_mapper(Role).relationships["staff"].uselist)
        self.assertEqual([person.first_name for person in physician.staff], ["Olivia", "Mia"])
        for person in staff:
            self.assertEqual([role.id for role in person.roles], [1])
        staff[1].roles = []
        self.assertEqual([role.id for role in staff[0].roles], [1])
        self.assertEqual([person.first_name for person in physician.staff], ["Olivia"])


if __name__ == "__main__":
    unittest.main()

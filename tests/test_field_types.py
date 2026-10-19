"""Validate API types and actual MySQL DDL without substituting a database."""

import base64
import unittest
from datetime import date
from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy.dialects.mysql import dialect
from sqlalchemy.schema import CreateTable
from sqlmodel import SQLModel

from app.images import DEFAULT_IMAGE, decode_image
from app.models.hospital import Hospital, HospitalCreate, HospitalUpdate
from app.models.patient import Patient, PatientCreate, PatientUpdate
from app.models.role import Role, RoleCreate, RoleUpdate
from app.models.staff import Staff, StaffCreate, StaffUpdate


class FieldTypeTests(unittest.TestCase):
    def test_salary_dates_and_patch_nulls(self):
        person = StaffCreate(first_name="Pat", last_name="Lee", hospital_id=1, date_of_admission=date(2020, 2, 29), salary=Decimal("0.10"))
        self.assertEqual(person.salary, Decimal("0.10"))
        self.assertEqual(person.model_dump(mode="json")["salary"], "0.10")
        changes = StaffUpdate.model_validate({"last_check_in": "2026-01-12T08:30:45-03:00"})
        self.assertEqual(changes.model_dump(mode="json")["last_check_in"], "2026-01-12T11:30:45")
        self.assertEqual(StaffUpdate().model_dump(exclude_unset=True), {})
        for payload in ({"salary": "1.001"}, {"salary": "10000000000.00"}, {"salary": "-0.01"}, {"salary": "NaN"}, {"salary": None}, {"date_of_admission": None}, {"date_of_admission": "2024-01-15T08:00:00"}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                StaffUpdate.model_validate(payload)
        self.assertEqual(StaffUpdate(last_check_in=None).model_dump(exclude_unset=True), {"last_check_in": None})

    def test_capacity_and_access_codes(self):
        self.assertEqual(HospitalCreate(name="Empty", location="City", capacity=0).capacity, 0)
        self.assertEqual(RoleCreate(name="Physician", access_type="A").access_type, "A")
        for model, payload in ((HospitalUpdate, {"capacity": -1}), (HospitalUpdate, {"capacity": 1.5}), (HospitalUpdate, {"capacity": None}), (RoleUpdate, {"access_type": "AB"}), (RoleUpdate, {"access_type": "D"}), (RoleUpdate, {"access_type": None})):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                model.model_validate(payload)

    def test_blob_transport_defaults_and_validation(self):
        encoded = base64.b64encode(DEFAULT_IMAGE).decode("ascii")
        payload = {"first_name": "Pat", "last_name": "Lee", "hospital_id": 1, "date_of_birth": "1990-01-01"}
        request = PatientCreate.model_validate({**payload, "image_blob": encoded})
        patient = Patient.model_validate(request, update={"image_blob": decode_image(request.image_blob)})
        self.assertEqual(patient.image_blob, DEFAULT_IMAGE)
        self.assertEqual(decode_image(None), DEFAULT_IMAGE)
        self.assertEqual(PatientUpdate().model_dump(exclude_unset=True), {})
        self.assertEqual(PatientUpdate(image_blob=None).model_dump(exclude_unset=True), {"image_blob": None})
        for image in ("bad", "data:image/png;base64," + encoded, base64.b64encode(b"<svg/>").decode(), base64.b64encode(b"x" * 65536).decode()):
            with self.subTest(image=image[:40]), self.assertRaises(ValidationError):
                PatientUpdate(image_blob=image)

    def test_mysql_column_types(self):
        hospital, role, staff, patient = [str(CreateTable(SQLModel.metadata.tables[model.__name__.lower()]).compile(dialect=dialect())) for model in (Hospital, Role, Staff, Patient)]
        self.assertIn("capacity INTEGER NOT NULL", hospital)
        self.assertIn("access_type CHAR(1) NOT NULL", role)
        self.assertIn("date_of_admission DATE NOT NULL", staff)
        self.assertIn("last_check_in DATETIME", staff)
        self.assertIn("salary NUMERIC(12, 2) NOT NULL", staff)
        self.assertIn("image_blob BLOB NOT NULL", patient)


if __name__ == "__main__":
    unittest.main()

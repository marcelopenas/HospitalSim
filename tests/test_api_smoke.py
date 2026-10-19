"""Integration tests for an explicitly configured, disposable MySQL schema."""

import base64
import os
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel, create_engine

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


class ApiSmokeTests(unittest.TestCase):
    def setUp(self):
        if not TEST_DATABASE_URL:
            self.skipTest(
                "Set TEST_DATABASE_URL to a disposable MySQL database ending in _test",
            )
        url = make_url(TEST_DATABASE_URL)
        if (
            url.drivername != "mysql+pymysql"
            or not url.database
            or not url.database.endswith("_test")
        ):
            msg = "TEST_DATABASE_URL must use mysql+pymysql and a disposable database ending in _test"
            raise ValueError(msg)
        os.environ["DATABASE_URL"] = TEST_DATABASE_URL
        from app.database import get_session
        from app.main import app

        self.engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
        self.addCleanup(self.engine.dispose)
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)
        self.addCleanup(SQLModel.metadata.drop_all, self.engine)

        def session_override():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = session_override
        self.addCleanup(app.dependency_overrides.clear)
        # Skip the production lifespan; this suite controls its own test tables.
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def create(self, resource, payload):
        defaults = {
            "/hospitals": {"capacity": 100},
            "/roles": {"access_type": "C"},
            "/staff": {"date_of_admission": "2024-01-15", "salary": "7500.00"},
        }
        payload = {**defaults.get(resource, {}), **payload}
        response = self.client.post(resource, json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_initialization_is_idempotent_and_persists_between_clients(self):
        self.assertEqual(
            self.client.get("/initialization").json(),
            {"was_initialized": False},
        )
        for _ in range(2):
            response = self.client.post("/initialization")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), {"was_initialized": True})
        other = TestClient(self.client.app)
        try:
            self.assertEqual(
                other.get("/initialization").json(),
                {"was_initialized": True},
            )
            self.assertEqual(other.get("/hospitals").json(), [])
        finally:
            other.close()

    def test_multiple_staff_keep_a_shared_role_after_new_assignments(self):
        hospital = self.create(
            "/hospitals",
            {"name": "Shared role hospital", "location": "Shared city"},
        )
        role = self.create("/roles", {"name": "Physician"})
        people = []
        for name in ("Olivia", "Mia"):
            people.append(
                self.create(
                    "/staff",
                    {
                        "first_name": name,
                        "last_name": "Example",
                        "hospital_id": hospital["id"],
                        "role_ids": [role["id"]],
                    },
                ),
            )
        for person in people:
            self.assertEqual(
                self.client.get(f"/staff/{person['id']}").json()["role_ids"],
                [role["id"]],
            )
        self.client.patch(f"/staff/{people[1]['id']}", json={"role_ids": []})
        self.assertEqual(
            self.client.get(f"/staff/{people[0]['id']}").json()["role_ids"],
            [role["id"]],
        )

    def test_health_and_documentation(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/docs").status_code, 200)
        paths = self.client.get("/openapi.json").json()["paths"]
        for resource in ("hospitals", "patients", "roles", "staff"):
            self.assertIn(f"/{resource}", paths)

    def test_relationship_chain_and_crud(self):
        hospital = self.create(
            "/hospitals",
            {"name": "Demo Hospital", "location": "Boston"},
        )
        role = self.create(
            "/roles",
            {"name": "Physician", "description": "Patient care"},
        )
        staff = self.create(
            "/staff",
            {
                "first_name": "Olivia",
                "last_name": "Chen",
                "hospital_id": hospital["id"],
                "role_ids": [role["id"]],
            },
        )
        self.assertEqual(staff["role_ids"], [role["id"]])
        patient = self.create(
            "/patients",
            {
                "first_name": "Alex",
                "last_name": "Taylor",
                "date_of_birth": "1990-05-12",
                "hospital_id": hospital["id"],
                "staff_id": staff["id"],
            },
        )
        for resource, record, changes in (
            (
                "patients",
                patient,
                {"first_name": "Alexandra", "staff_id": None},
            ),
            ("staff", staff, {"first_name": "Liv", "role_ids": []}),
            ("roles", role, {"description": "Clinical care"}),
            ("hospitals", hospital, {"location": "Cambridge"}),
        ):
            path = f"/{resource}/{record['id']}"
            self.assertEqual(len(self.client.get(f"/{resource}").json()), 1)
            self.assertEqual(self.client.get(path).status_code, 200)
            result = self.client.patch(path, json=changes)
            self.assertEqual(result.status_code, 200, result.text)
            for key, value in changes.items():
                self.assertEqual(result.json()[key], value)
        for resource, record in (
            ("patients", patient),
            ("staff", staff),
            ("roles", role),
            ("hospitals", hospital),
        ):
            path = f"/{resource}/{record['id']}"
            self.assertEqual(self.client.delete(path).status_code, 204)
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_reference_conflict_and_date_validation(self):
        a = self.create("/hospitals", {"name": "A", "location": "A City"})
        b = self.create("/hospitals", {"name": "B", "location": "B City"})
        self.assertEqual(
            self.client.post(
                "/hospitals",
                json={"name": "A", "location": "Elsewhere", "capacity": 100},
            ).status_code,
            409,
        )
        staff = self.create(
            "/staff",
            {"first_name": "Pat", "last_name": "Lee", "hospital_id": a["id"]},
        )
        data = {
            "first_name": "Alex",
            "last_name": "Taylor",
            "date_of_birth": "1990-01-01",
            "hospital_id": b["id"],
            "staff_id": staff["id"],
        }
        self.assertEqual(
            self.client.post("/patients", json=data).status_code,
            400,
        )
        data.update(hospital_id=a["id"], date_of_birth="2999-01-01")
        self.assertEqual(
            self.client.post("/patients", json=data).status_code,
            422,
        )

    def test_patch_nulls_and_relationship_guards(self):
        hospital = self.create(
            "/hospitals",
            {"name": "A", "location": "A City"},
        )
        destination = self.create(
            "/hospitals",
            {"name": "B", "location": "B City"},
        )
        role = self.create("/roles", {"name": "Physician"})
        staff = self.create(
            "/staff",
            {
                "first_name": "Olivia",
                "last_name": "Chen",
                "hospital_id": hospital["id"],
                "role_ids": [role["id"]],
            },
        )
        patient = self.create(
            "/patients",
            {
                "first_name": "Alex",
                "last_name": "Taylor",
                "date_of_birth": "1990-05-12",
                "hospital_id": hospital["id"],
                "staff_id": staff["id"],
            },
        )
        for resource, record, fields in (
            ("hospitals", hospital, ("name", "location", "capacity")),
            ("roles", role, ("name", "access_type")),
            (
                "staff",
                staff,
                (
                    "first_name",
                    "last_name",
                    "hospital_id",
                    "date_of_admission",
                    "salary",
                ),
            ),
            (
                "patients",
                patient,
                ("first_name", "last_name", "date_of_birth", "hospital_id"),
            ),
        ):
            path = f"/{resource}/{record['id']}"
            for field in fields:
                self.assertEqual(
                    self.client.patch(path, json={field: None}).status_code,
                    422,
                )
                self.assertEqual(self.client.get(path).json(), record)
            self.assertEqual(self.client.patch(path, json={}).json(), record)
        for resource, record in (
            ("hospitals", hospital),
            ("roles", role),
            ("staff", staff),
        ):
            self.assertEqual(
                self.client.delete(f"/{resource}/{record['id']}").status_code,
                409,
            )
        path = f"/staff/{staff['id']}"
        for roles in ({}, {"role_ids": None}, {"role_ids": []}):
            self.assertEqual(
                self.client.patch(
                    path,
                    json={"hospital_id": 999999, **roles},
                ).status_code,
                400,
            )
            self.assertEqual(
                self.client.patch(
                    path,
                    json={"hospital_id": destination["id"], **roles},
                ).status_code,
                409,
            )
            self.assertEqual(self.client.get(path).json(), staff)
        self.assertEqual(
            self.client.patch(
                f"/patients/{patient['id']}",
                json={"staff_id": None},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.patch(
                path,
                json={"hospital_id": destination["id"]},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.patch(
                f"/roles/{role['id']}",
                json={"description": None},
            ).status_code,
            200,
        )

    def test_new_fields_and_blob_round_trip(self):
        from decimal import Decimal

        from app.images import DEFAULT_IMAGE
        from app.models.patient import Patient
        from app.models.staff import Staff

        hospital = self.create(
            "/hospitals",
            {
                "name": "Typed hospital",
                "location": "Typed city",
                "capacity": 2,
            },
        )
        role = self.create("/roles", {"name": "Clinician", "access_type": "A"})
        self.assertEqual(role["access_type"], "A")
        person = self.create(
            "/staff",
            {
                "first_name": "Pat",
                "last_name": "Lee",
                "hospital_id": hospital["id"],
                "salary": "9999999999.99",
                "date_of_admission": "2020-02-29",
                "last_check_in": "2026-01-12T08:30:45-03:00",
            },
        )
        self.assertEqual(person["salary"], "9999999999.99")
        self.assertEqual(person["date_of_admission"], "2020-02-29")
        self.assertEqual(person["last_check_in"], "2026-01-12T11:30:45")
        image = base64.b64encode(DEFAULT_IMAGE).decode("ascii")
        patient = self.create(
            "/patients",
            {
                "first_name": "Alex",
                "last_name": "Lee",
                "hospital_id": hospital["id"],
                "date_of_birth": "1990-01-01",
                "image_blob": image,
            },
        )
        self.assertEqual(patient["image_blob"], image)
        with Session(self.engine) as session:
            saved_patient = session.get(Patient, patient["id"])
            saved_staff = session.get(Staff, person["id"])
            assert saved_patient is not None and saved_staff is not None
            self.assertEqual(saved_patient.image_blob, DEFAULT_IMAGE)
            self.assertEqual(saved_staff.salary, Decimal("9999999999.99"))
        path = f"/patients/{patient['id']}"
        self.assertEqual(
            self.client.patch(
                path,
                json={"image_blob": "not base64"},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.patch(path, json={"image_blob": None}).json()[
                "image_blob"
            ],
            image,
        )
        self.assertEqual(
            self.client.patch(
                f"/staff/{person['id']}",
                json={"salary": "0.10", "last_check_in": None},
            ).json()["salary"],
            "0.10",
        )
        self.assertIsNone(
            self.client.get(f"/staff/{person['id']}").json()["last_check_in"],
        )
        for field, value in (
            ("salary", "1.001"),
            ("salary", "-0.01"),
            ("date_of_admission", "2024-01-15T08:00:00"),
        ):
            self.assertEqual(
                self.client.patch(
                    f"/staff/{person['id']}",
                    json={field: value},
                ).status_code,
                422,
            )
        self.assertEqual(
            self.client.patch(
                f"/roles/{role['id']}",
                json={"access_type": "AB"},
            ).status_code,
            422,
        )

    def test_hospital_capacity_blocks_admission_transfer_and_shrinking(self):
        a = self.create(
            "/hospitals",
            {"name": "Capacity A", "location": "City A", "capacity": 1},
        )
        b = self.create(
            "/hospitals",
            {"name": "Capacity B", "location": "City B", "capacity": 1},
        )
        body = {
            "first_name": "Alex",
            "last_name": "Lee",
            "date_of_birth": "1990-01-01",
            "hospital_id": a["id"],
        }
        patient = self.create("/patients", body)
        self.assertEqual(
            self.client.post("/patients", json=body).status_code,
            409,
        )
        # Editing the existing patient in a full hospital does not consume a second slot.
        path = f"/patients/{patient['id']}"
        self.assertEqual(
            self.client.patch(
                path,
                json={"first_name": "Alexandra"},
            ).status_code,
            200,
        )
        other = self.create("/patients", {**body, "hospital_id": b["id"]})
        self.assertEqual(
            self.client.patch(path, json={"hospital_id": b["id"]}).status_code,
            409,
        )
        self.assertEqual(self.client.get(path).json()["hospital_id"], a["id"])
        self.assertEqual(
            self.client.patch(
                f"/hospitals/{a['id']}",
                json={"capacity": 0},
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.patch(
                f"/hospitals/{a['id']}",
                json={"capacity": -1},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.patch(
                f"/hospitals/{b['id']}",
                json={"capacity": 2},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.patch(path, json={"hospital_id": b["id"]}).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete(f"/patients/{other['id']}").status_code,
            204,
        )
        self.assertEqual(
            self.client.patch(
                f"/hospitals/{a['id']}",
                json={"capacity": 0},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post("/patients", json=body).status_code,
            409,
        )


if __name__ == "__main__":
    unittest.main()

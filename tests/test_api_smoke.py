"""Integration tests for an explicitly configured, disposable MySQL schema."""
import os
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlmodel import Session, SQLModel, create_engine

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


class ApiSmokeTests(unittest.TestCase):
    def setUp(self):
        if not TEST_DATABASE_URL:
            self.skipTest("Set TEST_DATABASE_URL to a disposable MySQL database ending in _test")
        url = make_url(TEST_DATABASE_URL)
        if url.drivername != "mysql+pymysql" or not url.database or not url.database.endswith("_test"):
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
        response = self.client.post(resource, json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_health_and_documentation(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/docs").status_code, 200)
        paths = self.client.get("/openapi.json").json()["paths"]
        for resource in ("hospitals", "patients", "roles", "staff"):
            self.assertIn(f"/{resource}", paths)

    def test_relationship_chain_and_crud(self):
        hospital = self.create("/hospitals", {"name": "Demo Hospital", "location": "Boston"})
        role = self.create("/roles", {"name": "Physician", "description": "Patient care"})
        staff = self.create("/staff", {"first_name": "Olivia", "last_name": "Chen", "hospital_id": hospital["id"], "role_ids": [role["id"]]})
        self.assertEqual(staff["role_ids"], [role["id"]])
        patient = self.create("/patients", {"first_name": "Alex", "last_name": "Taylor", "date_of_birth": "1990-05-12", "hospital_id": hospital["id"], "staff_id": staff["id"]})
        for resource, record, changes in (
            ("patients", patient, {"first_name": "Alexandra", "staff_id": None}),
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
        for resource, record in (("patients", patient), ("staff", staff), ("roles", role), ("hospitals", hospital)):
            path = f"/{resource}/{record['id']}"
            self.assertEqual(self.client.delete(path).status_code, 204)
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_reference_conflict_and_date_validation(self):
        a = self.create("/hospitals", {"name": "A", "location": "A City"})
        b = self.create("/hospitals", {"name": "B", "location": "B City"})
        self.assertEqual(self.client.post("/hospitals", json={"name": "A", "location": "Elsewhere"}).status_code, 409)
        staff = self.create("/staff", {"first_name": "Pat", "last_name": "Lee", "hospital_id": a["id"]})
        data = {"first_name": "Alex", "last_name": "Taylor", "date_of_birth": "1990-01-01", "hospital_id": b["id"], "staff_id": staff["id"]}
        self.assertEqual(self.client.post("/patients", json=data).status_code, 400)
        data.update(hospital_id=a["id"], date_of_birth="2999-01-01")
        self.assertEqual(self.client.post("/patients", json=data).status_code, 422)

    def test_patch_nulls_and_relationship_guards(self):
        hospital = self.create("/hospitals", {"name": "A", "location": "A City"})
        destination = self.create("/hospitals", {"name": "B", "location": "B City"})
        role = self.create("/roles", {"name": "Physician"})
        staff = self.create("/staff", {"first_name": "Olivia", "last_name": "Chen", "hospital_id": hospital["id"], "role_ids": [role["id"]]})
        patient = self.create("/patients", {"first_name": "Alex", "last_name": "Taylor", "date_of_birth": "1990-05-12", "hospital_id": hospital["id"], "staff_id": staff["id"]})
        for resource, record, fields in (
            ("hospitals", hospital, ("name", "location")),
            ("roles", role, ("name",)),
            ("staff", staff, ("first_name", "last_name", "hospital_id")),
            ("patients", patient, ("first_name", "last_name", "date_of_birth", "hospital_id")),
        ):
            path = f"/{resource}/{record['id']}"
            for field in fields:
                self.assertEqual(self.client.patch(path, json={field: None}).status_code, 422)
                self.assertEqual(self.client.get(path).json(), record)
            self.assertEqual(self.client.patch(path, json={}).json(), record)
        for resource, record in (("hospitals", hospital), ("roles", role), ("staff", staff)):
            self.assertEqual(self.client.delete(f"/{resource}/{record['id']}").status_code, 409)
        path = f"/staff/{staff['id']}"
        for roles in ({}, {"role_ids": None}, {"role_ids": []}):
            self.assertEqual(self.client.patch(path, json={"hospital_id": 999999, **roles}).status_code, 400)
            self.assertEqual(self.client.patch(path, json={"hospital_id": destination["id"], **roles}).status_code, 409)
            self.assertEqual(self.client.get(path).json(), staff)
        self.assertEqual(self.client.patch(f"/patients/{patient['id']}", json={"staff_id": None}).status_code, 200)
        self.assertEqual(self.client.patch(path, json={"hospital_id": destination["id"]}).status_code, 200)
        self.assertEqual(self.client.patch(f"/roles/{role['id']}", json={"description": None}).status_code, 200)



if __name__ == "__main__":
    unittest.main()

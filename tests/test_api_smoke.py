"""CRUD regression checks using isolated SQLite, not MySQL integration tests."""
import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.database import get_session
from app.main import app


class ApiSmokeTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        SQLModel.metadata.create_all(self.engine)

        def session_override():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = session_override
        # No context manager: skip the production database lifespan hook.
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

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


if __name__ == "__main__":
    unittest.main()

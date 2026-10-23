"""Exercise staff response schemas through FastAPI without a database server."""

import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session


class StaffResponseTests(unittest.TestCase):
    def setUp(self):
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "mysql+pymysql://localhost/hospitalsim_test"},
        ):
            from app.database import get_session
            from app.main import app

        self.session = MagicMock(spec=Session)
        self.session.exec.return_value.all.return_value = []
        app.dependency_overrides[get_session] = lambda: self.session
        self.addCleanup(app.dependency_overrides.clear)
        # The dependency is mocked and the production lifespan is not started.
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_empty_staff_list(self):
        response = self.client.get("/staff")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), [])

    def test_staff_list_and_item_preserve_salary_and_dates(self):
        from app.models.staff import Staff

        staff = Staff(
            id=1,
            first_name="Pat",
            last_name="Lee",
            hospital_id=1,
            date_of_admission=date(2024, 1, 15),
            salary=Decimal("7500.10"),
        )
        self.session.exec.return_value.all.return_value = [staff]
        self.session.get.return_value = staff
        expected = {
            "id": 1,
            "first_name": "Pat",
            "last_name": "Lee",
            "hospital_id": 1,
            "date_of_admission": "2024-01-15",
            "last_check_in": None,
            "salary": "7500.10",
            "role_ids": [],
        }
        for path, body in (("/staff", [expected]), ("/staff/1", expected)):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json(), body)

    def test_staff_request_validation_and_openapi(self):
        for method, path, payload in (
            ("POST", "/staff", {"salary": "invalid"}),
            ("PATCH", "/staff/1", {"salary": None}),
        ):
            with self.subTest(method=method):
                response = self.client.request(method, path, json=payload)
                self.assertEqual(response.status_code, 422, response.text)
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200, response.text)
        schemas = response.json()["components"]["schemas"]
        for name in ("StaffCreate", "StaffRead", "StaffUpdate"):
            self.assertIn("salary", schemas[name]["properties"])


if __name__ == "__main__":
    unittest.main()

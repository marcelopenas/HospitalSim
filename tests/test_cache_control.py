"""Exercise the cache policy through real HTTP responses without a database."""

import unittest

from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.caching import cache_control


class CacheControlTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.middleware("http")(cache_control)

        def read(request: Request):
            if "missing" in request.path_params.values():
                raise HTTPException(status_code=404, detail="Record not found")
            if request.query_params.get("conflict"):
                raise HTTPException(status_code=409, detail="Conflict")
            return {"ok": True}

        def missing():
            raise HTTPException(status_code=404, detail="Record not found")

        def invalid():
            raise HTTPException(status_code=409, detail="Conflict")

        for resource, identifier in (
            ("roles", "role_id"),
            ("hospitals", "hospital_id"),
            ("staff", "staff_id"),
            ("patients", "patient_id"),
        ):
            app.add_api_route(
                f"/{resource}",
                read,
                methods=["GET", "HEAD", "POST"],
            )
            app.add_api_route(
                f"/{resource}/{{{identifier}}}",
                read,
                methods=["GET", "PATCH", "DELETE"],
            )
            app.add_api_route(
                f"/{resource}/missing/record",
                missing,
                methods=["GET"],
            )
        app.add_api_route("/roles/conflict/write", invalid, methods=["PATCH"])
        app.add_api_route("/initialization", read, methods=["GET", "POST"])
        app.add_api_route("/health", read, methods=["GET"])
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_read_lifetimes_apply_to_collections_and_dynamic_item_routes(self):
        for resource, ttl in (
            ("roles", 300),
            ("hospitals", 60),
            ("staff", 15),
        ):
            for path in (
                f"/{resource}",
                f"/{resource}/123",
                f"/{resource}/456?example=true",
            ):
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(
                        response.headers["cache-control"],
                        f"private, max-age={ttl}, must-revalidate",
                    )
        self.assertEqual(
            self.client.head("/roles").headers["cache-control"],
            "private, max-age=300, must-revalidate",
        )

    def test_patients_initialization_and_writes_are_never_stored(self):
        for path in (
            "/patients",
            "/patients/123",
            "/patients/123?image=true",
            "/initialization",
            "/health",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    self.client.get(path).headers["cache-control"],
                    "no-store",
                )
        for resource in ("roles", "hospitals", "staff", "patients"):
            for method, path in (
                ("POST", f"/{resource}"),
                ("PATCH", f"/{resource}/123"),
                ("DELETE", f"/{resource}/123"),
            ):
                with self.subTest(method=method, path=path):
                    self.assertEqual(
                        self.client.request(method, path).headers[
                            "cache-control"
                        ],
                        "no-store",
                    )
        self.assertEqual(
            self.client.post("/initialization").headers["cache-control"],
            "no-store",
        )

    def test_errors_and_redirects_do_not_inherit_read_lifetimes(self):
        for path in (
            "/roles/missing",
            "/hospitals/missing",
            "/staff/missing",
            "/roles/missing/record",
            "/patients/missing/record",
            "/unknown",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.headers["cache-control"], "no-store")
        response = self.client.get("/roles?conflict=true")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.headers["cache-control"], "no-store")
        response = self.client.patch("/roles/conflict/write")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.headers["cache-control"], "no-store")
        response = self.client.get("/roles/", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["cache-control"], "no-store")


if __name__ == "__main__":
    unittest.main()

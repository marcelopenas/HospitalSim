"""Browser-cache policy for successful CRUD reads
no server-side result cache."""
from typing import TYPE_CHECKING

from fastapi import status

if TYPE_CHECKING:
    from fastapi import Request, Response
    from starlette.middleware.base import RequestResponseEndpoint

# Match resolved route templates so item IDs and query strings share the policy
CACHE_TTL_SECONDS = {
    "/roles": 300,
    "/roles/{role_id}": 300,
    "/hospitals": 60,
    "/hospitals/{hospital_id}": 60,
    "/staff": 15,
    "/staff/{staff_id}": 15,
}


async def cache_control(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    response = await call_next(request)
    route_path = getattr(request.scope.get("route"), "path", "")
    ttl = CACHE_TTL_SECONDS.get(route_path, 0)
    if (
        request.method in {"GET", "HEAD"}
        and response.status_code == status.HTTP_200_OK
        and ttl
    ):
        response.headers["Cache-Control"] = (
            f"private, max-age={ttl}, must-revalidate"
        )
    else:
        # Patients, initialization, writes, handled errors, and unlisted routes
        response.headers["Cache-Control"] = "no-store"
    return response

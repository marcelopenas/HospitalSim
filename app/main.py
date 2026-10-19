from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routers import hospitals, initialization, patients, roles, staff


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    yield


app = FastAPI(
    title="Hospital Simulation API",
    description="CRUD API for hospitals, staff, roles, and patients.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(hospitals.router)
app.include_router(patients.router)
app.include_router(roles.router)
app.include_router(staff.router)
app.include_router(initialization.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

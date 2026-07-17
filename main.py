from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routers import students, users

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create database tables when the local development server starts."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="SkillBridge API",
    description="Backend API for the SkillBridge campus talent match MVP.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(students.router)


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    """Confirm that the API is running."""
    return {"message": "SkillBridge API is running"}

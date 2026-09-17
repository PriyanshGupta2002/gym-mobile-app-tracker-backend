from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.gym import router as gym_router
from app.api.location import router as location_router
from app.api.membership import router as membership_router
from app.api.attendance import router as attendance_router
from app.api.membership_plan import router as membership_plan_router

app = FastAPI(
    title="GymApp API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production, see below
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(gym_router)
app.include_router(location_router)
app.include_router(membership_router)
app.include_router(attendance_router)
app.include_router(membership_plan_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

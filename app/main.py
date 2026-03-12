from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from .database import init_db
from .auth_router import router as auth_router
from .software_router import router as software_router
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload directory exists
    os.makedirs("uploads/id_proofs", exist_ok=True)
    # Initialize MongoDB
    await init_db()
    yield

app = FastAPI(
    title="SoulSoil Backend",
    description="Backend API for SoulSoil project using FastAPI and MongoDB",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory to serve files (optional but useful)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Routers
app.include_router(auth_router)
app.include_router(software_router)

@app.get("/")
async def root():
    return {"message": "Welcome to SoulSoil Backend API"}

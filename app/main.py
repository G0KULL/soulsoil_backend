from fastapi import FastAPI
from .database import engine, Base
from . import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SoulSoil Backend",
    description="Backend API for SoulSoil project using FastAPI and PostgreSQL",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to SoulSoil Backend API"}

# I will add routers for auth, users, etc. in further steps

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/soulsoil")

async def init_db():
    client = AsyncIOMotorClient(DATABASE_URL)
    # Extract database name from connection string or default to 'soulsoil'
    default_db = client.get_default_database()
    db_name = default_db.name if default_db is not None else "soulsoil"
    from .models import User, AgricultureSoftware
    await init_beanie(database=client[db_name], document_models=[User, AgricultureSoftware])

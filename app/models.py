from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from beanie import Document, Indexed
from pydantic import EmailStr, Field

class IDProofType(str, Enum):
    aadhaar = "aadhaar"
    passport = "passport"
    emirates_id = "emirates_id"

class UserRole(str, Enum):
    farmer = "farmer"
    investor = "investor"
    admin = "admin"

class User(Document):
    fullname: str
    email: EmailStr = Indexed(unique=True)
    mobile_number: Optional[str] = Indexed(unique=True)
    hashed_password: Optional[str] = None # Optional for social logins
    role: UserRole = UserRole.farmer # Default to farmer
    
    # New registration fields
    address: Optional[str] = None
    nationality: Optional[str] = None
    id_proof_type: Optional[IDProofType] = None
    id_proof_url: Optional[str] = None # Store path to uploaded file
    gst_number: Optional[str] = None
    
    # Verification status
    is_email_verified: bool = False
    is_phone_verified: bool = False
    
    # Social and OTP login fields
    social_provider: Optional[str] = None # 'google', 'facebook'
    social_id: Optional[str] = None
    otp: Optional[str] = None
    otp_expiry: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"

class AgricultureSoftware(Document):
    title: str
    description: str
    image_url: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agriculture_software"

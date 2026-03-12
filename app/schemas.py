from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from beanie import PydanticObjectId
from .models import IDProofType

class UserBase(BaseModel):
    email: EmailStr
    fullname: str
    mobile_number: Optional[str] = None
    address: Optional[str] = None
    nationality: Optional[str] = None
    id_proof_type: Optional[IDProofType] = None
    gst_number: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None # Optional because social signup might not have password

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    password: Optional[str] = None

class SocialLogin(BaseModel):
    token: str
    provider: str # 'google' or 'facebook'

class OTPRequest(BaseModel):
    mobile_number: str

class OTPVerify(BaseModel):
    mobile_number: str
    otp: str

class EmailVerify(BaseModel):
    email: EmailStr
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None

class ResetPassword(BaseModel):
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    otp: str
    new_password: str

class UserResponse(UserBase):
    id: PydanticObjectId = Field(alias="_id")
    is_email_verified: bool
    is_phone_verified: bool
    id_proof_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    id: Optional[str] = None

class AgricultureSoftwareCreate(BaseModel):
    title: str
    description: str

class AgricultureSoftwareResponse(BaseModel):
    id: PydanticObjectId = Field(alias="_id")
    title: str
    description: str
    image_url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

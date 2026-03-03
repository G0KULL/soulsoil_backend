from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    fullname: str

class UserCreate(UserBase):
    password: str
    mobile_number: Optional[str] = None

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    password: str

    # Ensure either email or mobile_number is provided
    def check_at_least_one(self):
        if not self.email and not self.mobile_number:
            raise ValueError("Either email or mobile_number must be provided")
        return self

class UserSchema(UserBase):
    id: int
    mobile_number: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

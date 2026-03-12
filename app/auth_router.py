from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime, timedelta, timezone
import shutil
import os
import random
import string
from jose import JWTError, jwt
from .models import User, IDProofType
from .schemas import (
    UserResponse, OTPRequest, OTPVerify, SocialLogin, 
    EmailVerify, UserLogin, Token, TokenData,
    ForgotPasswordRequest, ResetPassword
)
from .security import (
    get_password_hash, verify_password, create_access_token, 
    SECRET_KEY, ALGORITHM
)
from pydantic import EmailStr
from .mail import send_otp_email

def generate_otp(length: int = 6) -> str:
    """Generates a random numeric OTP of specified length."""
    return "".join(random.choices(string.digits, k=length))

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

UPLOAD_DIR = "uploads/id_proofs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = await User.get(token_data.id)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register(
    fullname: str = Form(...),
    email: EmailStr = Form(...),
    mobile_number: str = Form(...),
    password: str = Form(...),
    address: Optional[str] = Form(None),
    nationality: Optional[str] = Form(None),
    id_proof_type: IDProofType = Form(...),
    gst_number: Optional[str] = Form(None),
    id_proof_file: UploadFile = File(...)
):
    # Normalize email
    email = email.lower()

    # Check if user already exists
    if await User.find_one(User.email == email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if await User.find_one(User.mobile_number == mobile_number):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Save file
    file_extension = os.path.splitext(id_proof_file.filename)[1]
    filename = f"{mobile_number}_{datetime.now().timestamp()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(id_proof_file.file, buffer)

    # Create user with hashed password
    user = User(
        fullname=fullname,
        email=email,
        mobile_number=mobile_number,
        hashed_password=get_password_hash(password),
        address=address,
        nationality=nationality,
        id_proof_type=id_proof_type,
        id_proof_url=file_path,
        gst_number=gst_number
    )
    
    await user.insert()
    return user

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    # Find user by email or mobile
    user = None
    if credentials.email:
        email = credentials.email.lower()
        user = await User.find_one(User.email == email)
    elif credentials.mobile_number:
        user = await User.find_one(User.mobile_number == credentials.mobile_number)
    
    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/otp/send")
async def send_otp(request: OTPRequest):
    otp = generate_otp()
    user = await User.find_one(User.mobile_number == request.mobile_number)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.otp = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    await user.save()
    
    return {"message": f"OTP sent successfully: {otp}", "mobile": request.mobile_number}

@router.post("/otp/verify", response_model=Token)
async def verify_otp(request: OTPVerify):
    user = await User.find_one(User.mobile_number == request.mobile_number)
    
    if not user or not user.otp:
        raise HTTPException(status_code=400, detail="No OTP requested")
    
    if user.otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if user.otp_expiry and user.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")
    
    user.is_phone_verified = True
    user.otp = None 
    await user.save()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/social-login", response_model=Token)
async def social_login(request: SocialLogin):
    # Mock social login verification
    # Provider: google or facebook
    provider = request.provider.lower()
    if provider not in ["google", "facebook"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    # In a real app, you would:
    # 1. Verify 'token' with provider's API
    # 2. Get email and social_id from provider
    # 3. Find user or create if new
    
    # Mocking a search
    user = await User.find_one(User.email == "social_user@example.com") # Dummy check
    if not user:
        # Create dummy social user for demo
        user = User(
            fullname=f"{provider.capitalize()} User",
            email="social_user@example.com",
            social_provider=provider,
            social_id="social123",
            is_email_verified=True
        )
        await user.insert()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/email/send-otp")
async def send_email_otp(request: OTPRequest):
    # This expects mobile_number but we want email in request
    # Actually schema OTPRequest has mobile_number. Let's use EmailVerify schema or similar?
    # Better yet, let's just use request.mobile_number string as email if it looks like one,
    # or add a new schema. For now, I'll use request.mobile_number as a generic identity.
    identity = request.mobile_number
    user = None
    if "@" in identity:
        user = await User.find_one(User.email == identity.lower())
    else:
        user = await User.find_one(User.mobile_number == identity)
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    otp = generate_otp()
    user.otp = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    await user.save()
    
    email_sent = False
    if "@" in identity:
        email_sent = await send_otp_email(identity, otp, type="verification")
    
    return {
        "message": "OTP sent successfully" + (" to your email" if email_sent else ""),
        "otp": otp if not email_sent else None
    }

@router.post("/email/verify")
async def verify_email(request: EmailVerify):
    email = request.email.lower()
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.otp:
        raise HTTPException(status_code=400, detail="No OTP requested")
    
    if user.otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    if user.otp_expiry and user.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification code expired")

    user.is_email_verified = True
    user.otp = None
    await user.save()
    return {"message": "Email verified successfully"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    user = None
    if request.email:
        email = request.email.lower()
        user = await User.find_one(User.email == email)
    elif request.mobile_number:
        user = await User.find_one(User.mobile_number == request.mobile_number)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    otp = generate_otp()
    user.otp = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    await user.save()
    
    # Try to send real email if identity is email
    email_sent = False
    if request.email:
        email_sent = await send_otp_email(email, otp, type="password_reset")
    
    message = f"Reset code sent successfully"
    if email_sent:
        message += " to your email"
    else:
        message += f": {otp}" # Fallback to showing it if email fails or it's mobile
        
    return {"message": message, "identity": request.email or request.mobile_number}

@router.post("/reset-password")
async def reset_password(request: ResetPassword):
    user = None
    if request.email:
        email = request.email.lower()
        user = await User.find_one(User.email == email)
    elif request.mobile_number:
        user = await User.find_one(User.mobile_number == request.mobile_number)
    
    if not user or not user.otp:
        raise HTTPException(status_code=400, detail="No reset request found")
    
    if user.otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    if user.otp_expiry and user.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset code expired")
    
    user.hashed_password = get_password_hash(request.new_password)
    user.otp = None
    await user.save()
    
    return {"message": "Password reset successfully"}

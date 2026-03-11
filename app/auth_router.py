from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime, timedelta, timezone
import shutil
import os
from jose import JWTError, jwt
from .models import User, IDProofType
from .schemas import (
    UserResponse, OTPRequest, OTPVerify, SocialLogin, 
    EmailVerify, UserLogin, Token, TokenData
)
from .security import (
    get_password_hash, verify_password, create_access_token, 
    SECRET_KEY, ALGORITHM
)
from pydantic import EmailStr

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
        user = await User.find_one(User.email == credentials.email)
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
    otp = "123456" # Mock OTP
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
    
    if user.otp_expiry < datetime.now(timezone.utc):
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

@router.post("/email/verify")
async def verify_email(request: EmailVerify):
    user = await User.find_one(User.email == request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Mock email code: 654321
    if request.otp == "654321":
        user.is_email_verified = True
        await user.save()
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification code")

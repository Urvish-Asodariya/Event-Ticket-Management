from fastapi import APIRouter, status, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone, timedelta
from utils.config import settings
from utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_access_token,
)
from utils.mongodb import db
from models.user import UserCreate, User, UserLogin

router = APIRouter()


@router.post("/register", response_model=User)
async def register(user: UserCreate, request: Request):

    if await db.users.find_one({"email": str(user.email)}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    zone_id = request.query_params.get("zone_id")
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.now(timezone.utc)
    user_dict["updated_at"] = datetime.now(timezone.utc)
    user_dict["zone_id"] = zone_id
    result = await db.users.insert_one(user_dict)
    if result:
        return JSONResponse({"message": "User registered successfully"})
    else:
        return JSONResponse({"message": "User registration failed"})


@router.post("/login")
async def login(request: Request, credentials: UserLogin):
    try:
        email = credentials.email
        password = credentials.password

        try:
            user_dict = await db.users.find_one({"email": str(email)})
        except Exception as e:
            print(e)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "data": "User does not exist with this email",
                },
            )
        encrypted_password = user_dict.get("password")
        if not user_dict or not verify_password(password, encrypted_password):
            print("Incorrect email or password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(hours=int(settings.ACCESS_TOKEN_EXPIRE_TIME))
        print(access_token_expires)
        access_token = create_access_token(
            user_dict=user_dict, expires_delta=access_token_expires
        )
        print(access_token)
        return {"Token": access_token}
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": False, "data": "Internal Server Error"},
        )


@router.post("/verify-otp")
async def verify_otp(phone: str, otp: str):
    return {"status": "success", "message": "OTP verified successfully"}

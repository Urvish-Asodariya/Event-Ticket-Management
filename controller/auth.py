from fastapi import APIRouter, status, Request, HTTPException
from fastapi.responses import JSONResponse
from utils.serializers import serialize_doc, remove_password
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
from twilio.rest import Client

account_sid = settings.ACCOUNT_SID
auth_token = settings.AUTH_TOKEN
twilio_service_sid = settings.TWILIO_SERVICE_SID
client = Client(account_sid, auth_token)
fake_db = {}


async def register(user: UserCreate, request: Request):
    if await db.users.find_one({"email": str(user.email)}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    if await db.users.find_one({"phone": str(user.phone)}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered"
        )

    zone_id = request.query_params.get("zone_id")
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.now(timezone.utc)
    user_dict["updated_at"] = datetime.now(timezone.utc)
    user_dict["zone_id"] = zone_id
    user_dict["otp_verified"] = False 

    result = await db.users.insert_one(user_dict)
    if not result:
        raise HTTPException(status_code=500, detail="User registration failed")

    try:
        client.verify.v2.services(twilio_service_sid).verifications.create(
            to=user.phone, channel="sms"
        )
        await db.users.update_one(
            {"phone": user.phone},
            {"$set": {"otp_sent_at": datetime.now(timezone.utc)}}
        )
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")

    return JSONResponse({
        "message": "User registered successfully. OTP sent to your phone.",
        "phone": user.phone
    })


async def login(request: Request, credentials: UserLogin):
    email = credentials.email
    password = credentials.password

    try:
        user_dict = await db.users.find_one({"email": str(email)})
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error accessing user data"
        )

    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email",
        )
    
    if not user_dict.get("otp_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Phone number not verified. Please verify your phone first.",
        )

    encrypted_password = user_dict.get("password")
    if not verify_password(password, encrypted_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    access_token_expires = timedelta(hours=int(settings.ACCESS_TOKEN_EXPIRE_TIME))
    print(access_token_expires)
    access_token = create_access_token(
        user_dict=user_dict, expires_delta=access_token_expires
    )
    print(access_token)
    return {"Token": access_token}


async def verify_otp_controller(phone: str, otp_code: str):
    user = await db.users.find_one({"phone": phone})
    if not user:
        raise HTTPException(status_code=404, detail="User with this phone not found")
    try:
        verification_check = client.verify.v2.services(
            twilio_service_sid
        ).verification_checks.create(to=phone, code=otp_code)

        if verification_check.status == "approved":
            if phone in fake_db:
                fake_db[phone]["otp_verified"] = True
                fake_db[phone]["otp_verified_at"] = datetime.now()
            return {"status": "success", "message": "OTP verified successfully"}
        else:
            return {"status": "failed", "message": "Invalid OTP"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

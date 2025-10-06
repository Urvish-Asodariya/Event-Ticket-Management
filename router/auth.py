from fastapi import APIRouter, Request
from models.user import User, UserCreate, UserLogin
from controller.auth import register, login, verify_otp_controller

router = APIRouter()


@router.post("/register")
async def registerUser(user: UserCreate, request: Request):
    zone_id = request.query_params.get("zone_id")
    return await register(user, zone_id)


@router.post("/login")
async def loginUser(request: Request, credentials: UserLogin):
    return await login(credentials)


@router.post("/verify")
async def verify_otp(phone: str, otp: str):
    return await verify_otp_controller(phone, otp)

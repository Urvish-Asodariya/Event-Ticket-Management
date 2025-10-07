from fastapi import APIRouter, status, Request, HTTPException
from models.user import User, UserCreate, UserLogin, OTPRequest, OTPVerifyRequest
from controller.auth import register, login, verify_otp_controller
router = APIRouter()


@router.post("/register")
async def registerUser(user: UserCreate, request: Request):
    try:
        return await register(user, request)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/login")
async def loginUser(request: Request, credentials: UserLogin):
    try:
        return await login(request, credentials)
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    

@router.post("/verify")
async def verify_otp(request: OTPVerifyRequest):
    try:
        return await verify_otp_controller(request.phone, request.otp_code)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

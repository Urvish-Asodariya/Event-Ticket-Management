from fastapi import APIRouter, status, Request, HTTPException, Depends
from models.user import UserInDB
from utils.security import get_current_user
from controller.validation import (
    validate_qr_controller,
    validate_group_member_entry_controller,
)

router = APIRouter()


@router.post("/validate-qr")
async def validate_qr(qr_code: str, current_user: UserInDB = Depends(get_current_user)):
    try:
        return await validate_qr_controller(qr_code, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/validate-group-entry/{booking_id}/{member_index}")
async def validate_group_entry(
    booking_id: str,
    member_index: int,
    current_user: UserInDB = Depends(get_current_user),
):
    try:
        return await validate_group_member_entry_controller(
            booking_id, member_index, current_user
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

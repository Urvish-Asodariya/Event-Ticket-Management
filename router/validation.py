from fastapi import APIRouter, Depends
from models.user import UserInDB
from utils.security import get_current_user
from controller.validation import validate_qr_controller, validate_group_member_entry_controller

router = APIRouter()


@router.post("/validate-qr")
async def validate_qr(qr_code: str, current_user: UserInDB = Depends(get_current_user)):
    return await validate_qr_controller(qr_code, current_user)


@router.post("/validate-group-entry/{booking_id}/{member_index}")
async def validate_group_entry(booking_id: str, member_index: int, current_user: UserInDB = Depends(get_current_user)):
    return await validate_group_member_entry_controller(booking_id, member_index, current_user)

from fastapi import APIRouter, status, Request, HTTPException, Depends
from typing import List

from models.user import UserInDB
from models.staff_sale import StaffSale
from utils.security import get_current_user
from controller.staff import (
    verify_booking_controller,
    get_staff_sales_controller,
    get_staff_discounts_controller,
)

router = APIRouter()


@router.post("/verify-booking/{booking_id}")
async def verify_booking(
    booking_id: str, current_user: UserInDB = Depends(get_current_user)
):
    try:
        return await verify_booking_controller(booking_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/sales", response_model=List[StaffSale])
async def get_staff_sales(current_user: UserInDB = Depends(get_current_user)):
    try:
        return await get_staff_sales_controller(current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/active-discounts")
async def get_staff_discounts(current_user: UserInDB = Depends(get_current_user)):
    try:
        return await get_staff_discounts_controller(current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

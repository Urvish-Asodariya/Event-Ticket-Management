from fastapi import APIRouter, status, Request, HTTPException, Depends
from typing import List
from models.booking import BookingCreate, Booking, BookingUpdate
from models.user import UserInDB
from utils.security import get_current_user
from controller.bookings import (
    create_booking_controller,
    get_booking_controller,
    cancel_booking_controller,
    get_user_bookings_controller,
)

router = APIRouter()


@router.post("/{pass_id}", response_model=Booking)
async def create_booking(
    pass_id: str,
    booking: BookingCreate,
    current_user: UserInDB = Depends(get_current_user),
):
    try:
        return await create_booking_controller(pass_id,booking, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{booking_id}", response_model=Booking)
async def get_booking(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    try:
        return await get_booking_controller(booking_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/cancel/{booking_id}", response_model=Booking)
async def cancel_booking(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    try:
        return await cancel_booking_controller(booking_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/user/{user_id}", response_model=List[Booking])
async def get_user_bookings(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    try:
        return await get_user_bookings_controller(user_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

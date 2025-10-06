from fastapi import APIRouter, Depends
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


@router.post("/", response_model=Booking)
async def create_booking(
    booking: BookingCreate,
    current_user: UserInDB = Depends(get_current_user),
):
    return await create_booking_controller(booking, current_user)


@router.get("/{booking_id}", response_model=Booking)
async def get_booking(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    return await get_booking_controller(booking_id, current_user)


@router.put("/cancel/{booking_id}", response_model=Booking)
async def cancel_booking(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    return await cancel_booking_controller(booking_id, current_user)


@router.get("/user/{user_id}", response_model=List[Booking])
async def get_user_bookings(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    return await get_user_bookings_controller(user_id, current_user)

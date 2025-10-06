from typing import List
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime
from utils.mongodb import db
from models.user import UserInDB
from models.staff_sale import StaffSale


async def verify_booking_controller(booking_id: str, current_user: UserInDB) -> JSONResponse:
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Not authorized")

    booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking["zone_id"] != current_user.zone_id:
        raise HTTPException(status_code=403, detail="Booking does not belong to your zone")

    if booking["status"] != "active":
        raise HTTPException(status_code=400, detail="Booking already used or cancelled")

    await db["bookings"].update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": "used"}})

    staff_sale = {
        "staff_id": str(current_user.id),
        "booking_id": booking_id,
        "zone_id": current_user.zone_id,
        "payment_mode": "cash",
        "sale_time": datetime.utcnow(),
        "commission": None
    }
    await db["staff_sales"].insert_one(staff_sale)

    return JSONResponse({"message": "Booking verified successfully"})


async def get_staff_sales_controller(current_user: UserInDB) -> List[dict]:
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Not authorized")

    sales = await db["staff_sales"].find({"staff_id": str(current_user.id)}).to_list(None)
    return sales


async def get_staff_discounts_controller(current_user: UserInDB) -> List[dict]:
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Not authorized")

    discounts = await db["discounts"].find({
        "assigned_to": str(current_user.id),
        "is_active": True,
        "expiry": {"$gt": datetime.utcnow()},
    }).to_list(None)

    return discounts

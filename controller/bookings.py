from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from utils.mongodb import db
from fastapi.responses import JSONResponse
from models.booking import BookingCreate, BookingInDB, Booking, BookingUpdate
from models.user import UserInDB
from utils.security import get_current_user
from utils.qr_service import generate_qr_code
from bson import ObjectId
import qrcode
import base64
from datetime import datetime
from io import BytesIO

async def create_booking_controller(
    booking: BookingCreate, current_user: UserInDB = Depends(get_current_user)
):
    pass_ = await db["passes"].find_one({"_id": ObjectId(booking.pass_id)})
    if not pass_ or not pass_["is_active"]:
        raise HTTPException(status_code=404, detail="Pass not found or inactive")

    if booking.zone_id != pass_["zone_id"]:
        raise HTTPException(status_code=400, detail="Zone mismatch with pass")

    amount = pass_["price"]
    if booking.discount_applied:
        discount = await db["discounts"].find_one({
            "$or": [
                {"assigned_to": str(current_user.id)},
                {"zone_id": booking.zone_id}
            ],
            "is_active": True,
            "expiry": {"$gt": datetime.utcnow()},
        })

        if not discount or discount["percentage"] < booking.discount_applied:
            raise HTTPException(status_code=403, detail="Invalid or unauthorized discount")

        discount_value = amount * (booking.discount_applied / 100)
        if discount.get("max_limit") and discount_value > discount["max_limit"]:
            discount_value = discount["max_limit"]
        amount -= discount_value

        await db["discounts"].update_one(
            {"_id": discount["_id"]},
            {"$inc": {"times_used": 1}, "$addToSet": {"used_by": str(current_user.id)}}
        )

    booking_dict = booking.dict()
    booking_dict["_id"] = ObjectId()
    booking_dict["amount_paid"] = amount
    booking_dict["created_at"] = datetime.utcnow()
    booking_dict["user_id"] = current_user.id
    booking_dict["zone_id"] = booking.zone_id
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(str(booking_dict["_id"]))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    booking_dict["qr_code"] = base64.b64encode(buffered.getvalue()).decode()

    booking = await db["bookings"].insert_one(booking_dict)
    if booking.inserted_id:
        return JSONResponse({"message": "Booking created successfully"})
    else:
        return JSONResponse({"message": "Booking creation failed"})

async def get_booking_controller(
    booking_id: str, current_user: UserInDB = Depends(get_current_user)
):

    booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check if user owns the booking or is staff/admin
    if str(booking["user_id"]) != str(current_user.id) and current_user.role not in [
        "staff",
        "admin",
    ]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return Booking(**booking)

async def cancel_booking_controller(
    booking_id: str, current_user: UserInDB = Depends(get_current_user)
):

    booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check if user owns the booking or is admin
    if str(booking["user_id"]) != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if booking can be cancelled
    if booking["status"] != "active":
        raise HTTPException(
            status_code=400, detail="Only active bookings can be cancelled"
        )

    result = await db["bookings"].update_one(
        {"_id": ObjectId(booking_id)}, {"$set": {"status": "cancelled"}}
    )

    if result.modified_count == 1:
        return JSONResponse({"message": "Booking cancelled successfully"})
    else:
        return JSONResponse({"message": "Booking cancellation failed"})

async def get_user_bookings_controller(
    user_id: str, current_user: UserInDB = Depends(get_current_user)
):
    # Check if user is requesting their own bookings or is staff/admin
    if user_id != str(current_user.id) and current_user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")


    bookings = await db["bookings"].find({"user_id": user_id}).to_list(None)

    return bookings

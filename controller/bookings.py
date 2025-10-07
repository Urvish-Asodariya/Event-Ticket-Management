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
from utils.serializers import serialize_doc, serialize_list
from datetime import datetime
from io import BytesIO


async def create_booking_controller(
    pass_id: str,
    booking: BookingCreate,
    current_user: UserInDB = Depends(get_current_user),
):

    pass_ = await db["passes"].find_one({"_id": ObjectId(pass_id)})
    if not pass_:
        raise HTTPException(status_code=404, detail="Pass not found")

    if not pass_.get("is_active", False):
        raise HTTPException(status_code=400, detail="Pass is inactive")

    now = datetime.utcnow()
    validity_start = pass_.get("validity_start")
    validity_end = pass_.get("validity_end")

    if validity_end and now > validity_end:
        raise HTTPException(status_code=400, detail="Pass validity has expired")

    group_size_allowed = pass_.get("group_size", 0)
    booking_is_group = group_size_allowed > 1

    quantity_requested = 1
    if booking_is_group:
        if not booking.group_members or len(booking.group_members) == 0:
            raise HTTPException(
                status_code=400,
                detail="Group members required for group booking",
            )
        quantity_requested = len(booking.group_members)
        if quantity_requested > group_size_allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Group size exceeds allowed limit ({group_size_allowed})",
            )
    else:
        if booking.group_members and len(booking.group_members) > 1:
            raise HTTPException(
                status_code=400,
                detail="Single pass cannot include multiple group members",
            )

    available_quantity = pass_.get("available_quantity", 0)
    if available_quantity < quantity_requested:
        raise HTTPException(
            status_code=400,
            detail=f"Only {available_quantity} passes are available",
        )

    amount = pass_["price"] * quantity_requested
    zone_id = str(pass_.get("zone_id"))

    if not getattr(booking, "discount_applied", None) and pass_.get("pricing_rules"):
        for rule in pass_["pricing_rules"]:
            valid_until = rule.get("valid_until")
            if valid_until and now <= valid_until:
                if rule.get("discount_percentage"):
                    amount -= amount * (rule["discount_percentage"] / 100)
                elif rule.get("fixed_price") and rule["fixed_price"] > 0:
                    amount = rule["fixed_price"] * quantity_requested

    if getattr(booking, "discount_applied", None):
        discount = await db["discounts"].find_one({
            "$or": [
                {"assigned_to": str(current_user["_id"])},
                {"zone_id": zone_id},
            ],
            "is_active": True,
            "expiry": {"$gt": now},
        })

        if not discount or discount["percentage"] < booking.discount_applied:
            raise HTTPException(status_code=403, detail="Invalid or unauthorized discount")

        discount_value = amount * (booking.discount_applied / 100)
        if discount.get("max_limit") and discount_value > discount["max_limit"]:
            discount_value = discount["max_limit"]
        amount -= discount_value

        await db["discounts"].update_one(
            {"_id": discount["_id"]},
            {"$inc": {"times_used": 1}, "$addToSet": {"used_by": str(current_user["_id"])}}
        )

    booking_dict = booking.dict(exclude={"is_group"})
    booking_dict["_id"] = ObjectId()
    booking_dict["is_group"] = booking_is_group
    booking_dict["user_id"] = str(current_user["_id"])
    booking_dict["pass_id"] = str(pass_id)
    booking_dict["zone_id"] = zone_id
    booking_dict["amount_paid"] = amount
    booking_dict["status"] = "active"
    booking_dict["created_at"] = datetime.utcnow()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(str(booking_dict["_id"]))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    booking_dict["qr_code"] = base64.b64encode(buffered.getvalue()).decode()

    booking = await db["bookings"].insert_one(booking_dict)
    await db["passes"].update_one(
        {"_id": ObjectId(pass_id)},
        {"$inc": {"available_quantity": -quantity_requested}},
    )
    if booking.inserted_id:
        return JSONResponse({"message": "Booking created successfully"})
    else:
        return JSONResponse({"message": "Booking creation failed"})


async def get_booking_controller(
    booking_id: str, current_user: UserInDB = Depends(get_current_user)
):

    try:
        booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking ID format"
        )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if str(booking["user_id"]) != str(current_user.id) and current_user.role not in [
        "staff",
        "admin",
    ]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return serialize_doc(booking)


async def cancel_booking_controller(
    booking_id: str, current_user: UserInDB = Depends(get_current_user)
):

    try:
        booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking ID format"
        )

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

    return serialize_list(bookings)

from typing import List
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime
from utils.mongodb import db
from utils.serializers import  serialize_list
from models.user import UserInDB
from models.staff_sale import StaffSale


async def verify_booking_controller(booking_id: str, current_user: UserInDB) -> JSONResponse:
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format"
        )
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
    return serialize_list(sales)


async def get_staff_discounts_controller(current_user: UserInDB) -> List[dict]:
    if current_user.role != "staff":
        raise HTTPException(status_code=403, detail="Not authorized")

    discounts = await db["discounts"].find({
        "assigned_to": str(current_user.id),
        "is_active": True,
        "expiry": {"$gt": datetime.utcnow()},
    }).to_list(None)

    return serialize_list(discounts)

async def get_staff_stats_controller(current_user: UserInDB) -> dict:
    """Get statistics for the current staff member"""
    if current_user.role != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    total_sales = await db["staff_sales"].count_documents(
        {"staff_id": str(current_user.id)}
    )

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_sales = await db["staff_sales"].count_documents({
        "staff_id": str(current_user.id),
        "sale_time": {"$gte": today_start}
    })

    pipeline = [
        {"$match": {"staff_id": str(current_user.id)}},
        {"$group": {
            "_id": None,
            "total_commission": {"$sum": "$commission"},
            "total_discount_applied": {"$sum": "$discount_applied"}
        }}
    ]
    
    commission_data = await db["staff_sales"].aggregate(pipeline).to_list(None)
    
    return {
        "total_sales": total_sales,
        "today_sales": today_sales,
        "total_commission": commission_data[0].get("total_commission", 0) if commission_data else 0,
        "total_discount_applied": commission_data[0].get("total_discount_applied", 0) if commission_data else 0
    }
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from models.zone import Zone
from utils.mongodb import db
from models.user import UserInDB
from models.discount import DiscountCreate, Discount
from models.booking import Booking
from utils.security import check_admin_user
from bson import ObjectId

router = APIRouter()

def serialize_zone(zone):
    zone["_id"] = str(zone["_id"])
    return zone

@router.get("/users", response_model=List[UserInDB])
async def list_users(
    current_user: UserInDB = Depends(check_admin_user), skip: int = 0, limit: int = 100
):
    users = (
        await db["users"].find({"role": "user"}).skip(skip).limit(limit).to_list(None)
    )
    return users


@router.get("/staffs", response_model=List[UserInDB])
async def list_users(
    current_user: UserInDB = Depends(check_admin_user), skip: int = 0, limit: int = 100
):
    staffs = (
        await db["users"].find({"role": "staff"}).skip(skip).limit(limit).to_list(None)
    )
    return staffs


@router.get("/", response_model=List[Zone])
async def list_zones(current_admin: UserInDB = Depends(check_admin_user)):
    zones = await db.zones.find().to_list(None)
    return [serialize_zone(z) for z in zones]


@router.get("/staff-sales")
async def get_staff_sales_report(
    current_user: UserInDB = Depends(check_admin_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    query = {}
    if start_date or end_date:
        query["sale_time"] = {}
        if start_date:
            query["sale_time"]["$gte"] = start_date
        if end_date:
            query["sale_time"]["$lte"] = end_date

    pipeline = [
        {"$match": query},
        {
            "$lookup": {
                "from": "bookings",
                "localField": "booking_id",
                "foreignField": "_id",
                "as": "booking_info",
            }
        },
        {"$unwind": "$booking_info"},
        {
            "$group": {
                "_id": "$staff_id",
                "total_sales": {"$sum": 1},
                "total_amount": {"$sum": "$booking_info.amount_paid"},
                "total_discount": {"$sum": "$discount_applied"},
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "_id",
                "foreignField": "_id",
                "as": "staff_info",
            }
        },
    ]

    staff_sales = await db["staff_sales"].aggregate(pipeline).to_list(None)
    return staff_sales


@router.get("/stats")
async def get_stats(
    current_user: UserInDB = Depends(check_admin_user),
    period: str = "today",
):
    end_date = datetime.utcnow()
    if period == "today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = end_date - timedelta(days=end_date.weekday())  # start of week
    elif period == "month":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.min

    pipeline = [
        {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
        {
            "$group": {
                "_id": None,
                "total_bookings": {"$sum": 1},
                "total_revenue": {"$sum": "$amount_paid"},
                "total_attendance": {
                    "$sum": {"$cond": [{"$eq": ["$status", "used"]}, 1, 0]}
                },
                "online_bookings": {
                    "$sum": {"$cond": [{"$eq": ["$sold_by", "online"]}, 1, 0]}
                },
                "offline_bookings": {
                    "$sum": {"$cond": [{"$ne": ["$sold_by", "online"]}, 1, 0]}
                },
            }
        },
    ]

    stats = await db["bookings"].aggregate(pipeline).to_list(None)
    return (
        stats[0]
        if stats
        else {
            "total_bookings": 0,
            "total_revenue": 0,
            "total_attendance": 0,
            "online_bookings": 0,
            "offline_bookings": 0,
        }
    )


@router.post("/discounts", response_model=Discount)
async def create_discount(
    discount: DiscountCreate, current_user: UserInDB = Depends(check_admin_user)
):
    if await db["discounts"].find_one({"code": discount.code}):
        raise HTTPException(status_code=400, detail="Discount code already exists")
    if discount.assigned_to:
        staff = await db["users"].find_one(
            {"_id": ObjectId(discount.assigned_to), "role": "staff"}
        )
        if not staff:
            raise HTTPException(status_code=404, detail="Staff member not found")
    discount_dict = discount.dict()
    discount_dict["_id"] = ObjectId()
    discount_dict["created_at"] = datetime.utcnow()
    discount_dict["is_active"] = True
    discount_dict["times_used"] = 0
    discount_dict["used_by"] = []
    discount_dict["zone_id"] = (
        discount_dict.get("zone_id") if "zone_id" in discount_dict else None
    )

    await db["discounts"].insert_one(discount_dict)
    return Discount(**discount_dict)


@router.get("/group-bookings")
async def get_group_bookings(
    current_user: UserInDB = Depends(check_admin_user), status: Optional[str] = None
):
    query = {"is_group": True}
    if status:
        query["status"] = status
    group_bookings = await db["bookings"].find(query).to_list(None)
    return group_bookings


@router.get("/bookings", response_model=List[Booking])
async def get_all_bookings(
    current_user: UserInDB = Depends(check_admin_user),
    zone_id: Optional[str] = None,
    status: Optional[str] = None,
):
    query = {}
    if zone_id:
        query["zone_id"] = zone_id
    if status:
        query["status"] = status
    bookings = await db["bookings"].find(query).to_list(None)
    return bookings


@router.get("/discounts")
async def get_discounts(
    current_user: UserInDB = Depends(check_admin_user), zone_id: Optional[str] = None
):
    query = {}
    if zone_id:
        query["zone_id"] = zone_id
    discounts = await db["discounts"].find(query).to_list(None)
    return discounts

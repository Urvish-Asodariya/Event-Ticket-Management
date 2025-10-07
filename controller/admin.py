from typing import List, Optional, Dict
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException
from utils.serializers import serialize_doc, serialize_list, remove_password
from utils.mongodb import db
from models.user import UserInDB
from models.zone import Zone
from models.discount import Discount, DiscountCreate
from models.booking import Booking


# -------------------- Users & Staff --------------------
async def list_users_controller(skip: int = 0, limit: int = 100) -> List[Dict]:
    users = await db["users"].find({"role": "user"}).skip(skip).limit(limit).to_list(None)
    users = serialize_list(users)
    users = remove_password(users)
    return users


async def list_staffs_controller(skip: int = 0, limit: int = 100) -> List[Dict]:
    staffs = await db["users"].find({"role": "staff"}).skip(skip).limit(limit).to_list(None)
    staffs = serialize_list(staffs)
    staffs = remove_password(staffs)
    return staffs


# -------------------- Zones --------------------
async def list_zones_controller() -> List[Dict]:
    zones = await db.zones.find().to_list(None)
    return serialize_list(zones)


# -------------------- Staff Sales Report --------------------
async def get_staff_sales_report_controller(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
    query = {}
    if start_date or end_date:
        query["sale_time"] = {}
        if start_date:
            query["sale_time"]["$gte"] = start_date
        if end_date:
            query["sale_time"]["$lte"] = end_date

    pipeline = [
        {"$match": query},
        {"$lookup": {"from": "bookings", "localField": "booking_id", "foreignField": "_id", "as": "booking_info"}},
        {"$unwind": "$booking_info"},
        {"$group": {
            "_id": "$staff_id",
            "total_sales": {"$sum": 1},
            "total_amount": {"$sum": "$booking_info.amount_paid"},
            "total_discount": {"$sum": "$discount_applied"},
        }},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "staff_info"}},
    ]
    staff_sales = await db["staff_sales"].aggregate(pipeline).to_list(None)
    return serialize_list(staff_sales)


# -------------------- Stats --------------------
async def get_stats_controller(period: str = "today") -> Dict:
    end_date = datetime.utcnow()
    if period == "today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = end_date - timedelta(days=end_date.weekday())
    elif period == "month":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.min

    pipeline = [
        {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": None,
            "total_bookings": {"$sum": 1},
            "total_revenue": {"$sum": "$amount_paid"},
            "total_attendance": {"$sum": {"$cond": [{"$eq": ["$status", "used"]}, 1, 0]}},
            "online_bookings": {"$sum": {"$cond": [{"$eq": ["$sold_by", "online"]}, 1, 0]}},
            "offline_bookings": {"$sum": {"$cond": [{"$ne": ["$sold_by", "online"]}, 1, 0]}},
        }},
    ]

    stats = await db["bookings"].aggregate(pipeline).to_list(None)
    if stats:
        result = stats[0]
        result.pop("_id", None)  
        return result
    
    return stats[0] if stats else {
        "total_bookings": 0,
        "total_revenue": 0,
        "total_attendance": 0,
        "online_bookings": 0,
        "offline_bookings": 0,
    }


# -------------------- Discounts --------------------
async def create_discount_controller(discount: DiscountCreate) -> Discount:
    if await db["discounts"].find_one({"code": discount.code}):
        raise HTTPException(status_code=400, detail="Discount code already exists")
    
    if discount.assigned_to:
        staff = await db["users"].find_one({"_id": ObjectId(discount.assigned_to), "role": "staff"})
        if not staff:
            raise HTTPException(status_code=404, detail="Staff member not found")

    discount_dict = discount.dict()
    discount_dict["_id"] = ObjectId()
    discount_dict["created_at"] = datetime.utcnow()
    discount_dict["is_active"] = True
    discount_dict["times_used"] = 0
    discount_dict["used_by"] = []
    discount_dict["zone_id"] = discount_dict.get("zone_id")

    await db["discounts"].insert_one(discount_dict)
    return serialize_doc(discount_dict)


async def get_discounts_controller(zone_id: Optional[str] = None) -> List[Dict]:
    query = {}
    if zone_id:
        query["zone_id"] = zone_id
    discounts = await db["discounts"].find(query).to_list(None)
    return serialize_list(discounts)


# -------------------- Bookings --------------------
async def get_group_bookings_controller(status: Optional[str] = None) -> List[Dict]:
    query = {"is_group": True}
    if status:
        query["status"] = status
    group_bookings = await db["bookings"].find(query).to_list(None)
    return serialize_list(group_bookings)


async def get_all_bookings_controller(zone_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    query = {}
    if zone_id:
        query["zone_id"] = zone_id
    if status:
        query["status"] = status
    bookings = await db["bookings"].find(query).to_list(None)
    return serialize_list(bookings)

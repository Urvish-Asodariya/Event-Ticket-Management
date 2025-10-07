from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict
from bson import ObjectId
from datetime import datetime
from utils.mongodb import db
from utils.serializers import serialize_doc, serialize_list
from models.zone import ZoneCreate, ZoneUpdate
from models.user import UserInDB


async def create_zone_controller(
    zone: ZoneCreate, current_admin: UserInDB
) -> dict:
    existing_zone = await db.zones.find_one({"name": zone.name})
    if existing_zone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Zone name already exists"
        )
    zone_dict = zone.dict()
    zone_dict["_id"] = ObjectId()
    zone_dict["created_at"] = datetime.utcnow()
    zone_dict["name"] = zone.name
    zone_dict["created_by"] = str(current_admin.id)
    zone_dict["description"] = zone.description
    zone_dict["is_active"] = True

    result = await db.zones.insert_one(zone_dict)
    if result.inserted_id:
        return JSONResponse({"message": "Zone created successfully"})
    return JSONResponse({"message": "Zone creation failed"})


async def get_zone_controller(zone_id: str, current_admin: UserInDB) -> Dict:
    zone = await db.zones.find_one({"_id": ObjectId(zone_id)})
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return serialize_doc(zone)


async def update_zone_controller(
    zone_id: str, zone: ZoneUpdate, current_admin: UserInDB
) -> Dict:
    zone_dict = zone.dict(exclude_unset=True)
    if not zone_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    zone_dict["updated_at"] = datetime.utcnow()
    zone_dict["updated_by"] = str(current_admin.id)
    try:
        result = await db.zones.update_one(
            {"_id": ObjectId(zone_id)}, {"$set": zone_dict}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid zone ID format"
        )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"message": "Zone updated successfully"}


async def delete_zone_controller(zone_id: str) -> Dict:
    active_passes = await db.passes.count_documents(
        {"zone_id": zone_id, "is_active": True}
    )

    if active_passes > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete zone with {active_passes} active passes",
        )

    try:
        result = await db.zones.delete_one({"_id": ObjectId(zone_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid zone ID format"
        )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found"
        )

    return {"message": "Zone deleted successfully"}


async def deactivate_zone_controller(zone_id: str, current_admin: UserInDB) -> Dict:
    try:
        result = await db.zones.update_one(
            {"_id": ObjectId(zone_id)},
            {
                "$set": {
                    "is_active": False,
                    "deactivated_at": datetime.utcnow(),
                    "deactivated_by": str(current_admin.id),
                }
            },
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid zone ID format"
        )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found"
        )

    return {"message": "Zone deactivated successfully"}

async def activate_zone_controller(
    zone_id: str, 
    current_admin: UserInDB
) -> dict:

    try:
        result = await db.zones.update_one(
            {"_id": ObjectId(zone_id)},
            {
                "$set": {
                    "is_active": True,
                    "reactivated_at": datetime.utcnow(),
                    "reactivated_by": str(current_admin.id)
                }
            }
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zone ID format"
        )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    return {"message": "Zone activated successfully"}


async def get_zone_stats_controller(zone_id: str) -> dict:
    """Get statistics for a specific zone"""
    try:
        zone = await db.zones.find_one({"_id": ObjectId(zone_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zone ID format"
        )
    
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )

    total_passes = await db.passes.count_documents({"zone_id": zone_id})
    active_passes = await db.passes.count_documents({
        "zone_id": zone_id,
        "is_active": True
    })
    
    total_bookings = await db.bookings.count_documents({"zone_id": zone_id})
    active_bookings = await db.bookings.count_documents({
        "zone_id": zone_id,
        "status": "active"
    })
    
    total_staff = await db.users.count_documents({
        "zone_id": zone_id,
        "role": "staff"
    })

    pipeline = [
        {"$match": {"zone_id": zone_id}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$amount_paid"}
        }}
    ]
    revenue_data = await db.bookings.aggregate(pipeline).to_list(None)
    
    return {
        "zone_id": str(zone["_id"]),
        "zone_name": zone["name"],
        "total_passes": total_passes,
        "active_passes": active_passes,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "total_staff": total_staff,
        "total_revenue": revenue_data[0]["total_revenue"] if revenue_data else 0
    }
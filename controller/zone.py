from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models.zone import ZoneCreate, Zone, ZoneUpdate
from models.user import UserInDB
from utils.security import check_admin_user
from utils.mongodb import db
from bson import ObjectId
from datetime import datetime

router = APIRouter()

def serialize_zone(zone):
    zone["_id"] = str(zone["_id"])
    return zone

@router.post("/", response_model=Zone)
async def create_zone(zone: ZoneCreate, current_admin: UserInDB = Depends(check_admin_user)):
    zone_dict = zone.dict()
    zone_dict["_id"] = ObjectId()
    zone_dict["created_at"] = datetime.utcnow()
    zone_dict["name"] = zone.name
    zone_dict["created_by"] = current_admin._id
    zone_dict["description"] = zone.description
    zone_dict["is_active"] = True
    await db.zones.insert_one(zone_dict)
    return Zone(**serialize_zone(zone_dict))

@router.get("/{zone_id}", response_model=Zone)
async def get_zone(zone_id: str, current_admin: UserInDB = Depends(check_admin_user)):
    zone = await db.zones.find_one({"_id": ObjectId(zone_id)})
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return Zone(**serialize_zone(zone))

@router.put("/{zone_id}", response_model=Zone)
async def update_zone(zone_id: str, zone: ZoneUpdate, current_admin: UserInDB = Depends(check_admin_user)):
    zone_dict = zone.dict()
    zone_dict["updated_at"] = datetime.utcnow()
    await db.zones.update_one({"_id": ObjectId(zone_id)}, {"$set": zone_dict})
    updated_zone = await db.zones.find_one({"_id": ObjectId(zone_id)})
    return Zone(**serialize_zone(updated_zone))

@router.delete("/{zone_id}")
async def delete_zone(zone_id: str, current_admin: UserInDB = Depends(check_admin_user)):
    await db.zones.delete_one({"_id": ObjectId(zone_id)})
    return {"message": "Zone deleted successfully"}

@router.put("/deactivate/{zone_id}")
async def deactivate_zone(zone_id: str, current_admin: UserInDB = Depends(check_admin_user)):
    await db.zones.update_one({"_id": ObjectId(zone_id)}, {"$set": {"is_active": False}})
    return {"message": "Zone deactivated successfully"}


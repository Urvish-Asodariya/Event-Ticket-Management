from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Dict
from bson import ObjectId
from datetime import datetime
from utils.mongodb import db
from models.zone import ZoneCreate, ZoneUpdate
from models.user import UserInDB

def serialize_pass(pass_doc):
    if not pass_doc:
        return None
    pass_doc["_id"] = str(pass_doc["_id"])
    return pass_doc

async def create_zone_controller(zone: ZoneCreate, current_admin: UserInDB) -> JSONResponse:
    zone_dict = zone.dict()
    zone_dict["_id"] = ObjectId()
    zone_dict["created_at"] = datetime.utcnow()
    zone_dict["name"] = zone.name
    zone_dict["created_by"] = current_admin["_id"]
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
    return zone


async def update_zone_controller(zone_id: str, zone: ZoneUpdate) -> Dict:
    zone_dict = zone.dict(exclude_unset=True)
    zone_dict["updated_at"] = datetime.utcnow()
    result = await db.zones.update_one({"_id": ObjectId(zone_id)}, {"$set": zone_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"message": "Zone updated successfully"}


async def delete_zone_controller(zone_id: str) -> Dict:
    await db.zones.delete_one({"_id": ObjectId(zone_id)})
    return {"message": "Zone deleted successfully"}


async def deactivate_zone_controller(zone_id: str) -> Dict:
    await db.zones.update_one({"_id": ObjectId(zone_id)}, {"$set": {"is_active": False}})
    return {"message": "Zone deactivated successfully"}

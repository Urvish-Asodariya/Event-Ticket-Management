from typing import Optional, List
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime

from utils.mongodb import db
from models.passes import PassCreate, PassUpdate
from models.user import UserInDB

def serialize_pass(pass_doc):
    if not pass_doc:
        return None
    pass_doc["_id"] = str(pass_doc["_id"])
    return pass_doc

async def list_passes_controller() -> List[dict]:
    passes = await db.passes.find({"is_active": True}).to_list(None)
    return [serialize_pass(p) for p in passes]

async def get_pass_controller(pass_id: str):
    pass_ = await db.passes.find_one({"_id": ObjectId(pass_id)})
    if not pass_:
        raise HTTPException(status_code=404, detail="Pass not found")
    return serialize_pass(pass_)


async def create_pass_controller(pass_: PassCreate, zone_id: Optional[str] = None) -> JSONResponse:
    pass_dict = pass_.dict()
    pass_dict["_id"] = ObjectId()
    pass_dict["created_at"] = datetime.utcnow()
    pass_dict["is_active"] = True
    pass_dict["zone_id"] = zone_id
    result = await db.passes.insert_one(pass_dict)
    if result.inserted_id:
        return JSONResponse({"message": "Pass created successfully"})
    return JSONResponse({"message": "Pass creation failed"})


async def create_group_pass_controller(pass_: PassCreate, zone_id: Optional[str] = None) -> JSONResponse:
    if not pass_.group_size or pass_.group_size < 2:
        raise HTTPException(status_code=400, detail="Group size must be at least 2")

    pass_.type = "group"
    pass_dict = pass_.dict()
    pass_dict["_id"] = ObjectId()
    pass_dict["created_at"] = datetime.utcnow()
    pass_dict["is_active"] = True
    pass_dict["zone_id"] = zone_id
    result = await db.passes.insert_one(pass_dict)
    if result.inserted_id:
        return JSONResponse({"message": "Group Pass created successfully"})
    return JSONResponse({"message": "Group Pass creation failed"})


async def update_pass_controller(pass_id: str, pass_update: PassUpdate) -> dict:
    update_data = pass_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.passes.update_one({"_id": ObjectId(pass_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return {"message": "Pass updated successfully"}


async def delete_pass_controller(pass_id: str) -> JSONResponse:
    result = await db.passes.delete_one({"_id": ObjectId(pass_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return JSONResponse({"message": "Pass deleted successfully"})


async def deactivate_pass_controller(pass_id: str) -> dict:
    result = await db.passes.update_one({"_id": ObjectId(pass_id)}, {"$set": {"is_active": False}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return {"message": "Pass deactivated successfully"}

async def activate_pass_controller(pass_id: str) -> dict:
    result = await db.passes.update_one({"_id": ObjectId(pass_id)}, {"$set": {"is_active": True}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return {"message": "Pass activated successfully"}
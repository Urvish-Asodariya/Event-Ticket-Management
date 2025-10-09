from typing import Optional, List
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime
from models.user import UserInDB
from utils.mongodb import db
from utils.serializers import serialize_doc, serialize_list
from models.passes import PassCreate, PassUpdate


async def list_passes_controller() -> List[dict]:
    passes = await db.passes.find({"is_active": True}).to_list(None)
    return serialize_list(passes)


async def get_pass_controller(pass_id: str):
    try:
        pass_ = await db.passes.find_one({"_id": ObjectId(pass_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pass ID format"
        )

    if not pass_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pass not found"
        )

    return serialize_doc(pass_)


async def create_pass_controller(
    current_admin: UserInDB, pass_: PassCreate, zone_id: Optional[str] = None
) -> JSONResponse:
    pass_dict = pass_.dict()
    pass_dict["_id"] = ObjectId()
    pass_dict["created_at"] = datetime.utcnow()
    pass_dict["is_active"] = True
    pass_dict["zone_id"] = zone_id
    pass_dict["created_by"] = str(current_admin.id)
    result = await db.passes.insert_one(pass_dict)
    if result.inserted_id:
        return JSONResponse({"message": "Pass created successfully"})
    return JSONResponse({"message": "Pass creation failed"})


async def create_group_pass_controller(
    current_admin: UserInDB, pass_: PassCreate, zone_id: Optional[str] = None
) -> JSONResponse:
    if not pass_.group_size or pass_.group_size < 2:
        raise HTTPException(status_code=400, detail="Group size must be at least 2")

    pass_.type = "group"
    pass_dict = pass_.dict()
    pass_dict["_id"] = ObjectId()
    pass_dict["created_at"] = datetime.utcnow()
    pass_dict["is_active"] = True
    pass_dict["zone_id"] = zone_id
    pass_dict["created_by"] = str(current_admin.id)
    result = await db.passes.insert_one(pass_dict)
    if result.inserted_id:
        return JSONResponse({"message": "Group Pass created successfully"})
    return JSONResponse({"message": "Group Pass creation failed"})


async def update_pass_controller(pass_id: str, pass_update: PassUpdate) -> dict:
    update_data = pass_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        result = await db.passes.update_one(
            {"_id": ObjectId(pass_id)}, {"$set": update_data}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pass ID format"
        )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return {"message": "Pass updated successfully"}


async def delete_pass_controller(pass_id: str) -> JSONResponse:
    try:
        result = await db.passes.delete_one({"_id": ObjectId(pass_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pass ID format"
        )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return JSONResponse({"message": "Pass deleted successfully"})


async def toggle_pass_controller(pass_id: str) -> dict:
    try:
        pass_doc = await db.passes.find_one({"_id": ObjectId(pass_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pass ID format"
        )

    if not pass_doc:
        raise HTTPException(status_code=404, detail="Pass not found")

    new_status = not pass_doc.get("is_active", False)
    update_data = {"is_active": new_status}

    if not new_status:
        update_data["deactivated_at"] = datetime.utcnow()
    else:
        update_data["deactivated_at"] = None

    result = await db.passes.update_one(
        {"_id": ObjectId(pass_id)}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to toggle pass status")

    status_str = "activated" if new_status else "deactivated"
    return {"message": f"Pass {status_str} successfully"}

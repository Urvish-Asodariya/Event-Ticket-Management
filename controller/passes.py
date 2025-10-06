from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from fastapi.responses import JSONResponse
from utils.mongodb import db
from models.passes import PassCreate, PassInDB, Pass, PassUpdate
from models.user import UserInDB
from utils.security import get_current_user, check_admin_user
from bson import ObjectId
from datetime import datetime

router = APIRouter()


def serialize_pass(pass_doc):
    if not pass_doc:
        return None
    pass_doc["_id"] = str(pass_doc["_id"])
    return pass_doc


@router.get("/", response_model=List[Pass])
async def list_passes():
    passes = await db.passes.find({"is_active": True}).to_list(None)
    return [serialize_pass(p) for p in passes]


@router.get("/{pass_id}", response_model=Pass)
async def get_pass(pass_id: str):
    pass_ = await db.passes.find_one({"_id": ObjectId(pass_id)})
    if not pass_:
        raise HTTPException(status_code=404, detail="Pass not found")
    return serialize_pass(pass_)


@router.post("/")
async def create_pass(
    pass_: PassCreate,
    current_user: UserInDB = Depends(check_admin_user),
    zone_id: Optional[str] = None,
):
    pass_dict = pass_.dict()
    pass_dict["_id"] = ObjectId()
    pass_dict["created_at"] = datetime.utcnow()
    pass_dict["is_active"] = True
    pass_dict["zone_id"] = zone_id
    result = await db.passes.insert_one(pass_dict)
    if result.inserted_id:
        return JSONResponse({"message": "Pass created successfully"})
    else:
        return JSONResponse({"message": "Pass creation failed"})


@router.post("/group")
async def create_group_pass(
    pass_: PassCreate,
    current_user: UserInDB = Depends(check_admin_user),
    zone_id: Optional[str] = None,
):

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
    else:
        return JSONResponse({"message": "Group Pass creation failed"})


@router.put("/{pass_id}", response_model=Pass)
async def update_pass(
    pass_id: str,
    pass_update: PassUpdate,
    current_user: UserInDB = Depends(check_admin_user),
):
    update_data = pass_update.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.passes.update_one(
        {"_id": ObjectId(pass_id)}, {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return {"message": "Pass updated successfully"}


@router.delete("/{pass_id}")
async def delete_pass(pass_id: str, current_user: UserInDB = Depends(check_admin_user)):
    result = await db.passes.delete_one({"_id": ObjectId(pass_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return JSONResponse({"message": "Pass deleted successfully"})


@router.post("/deactivate/{pass_id}")
async def deactivate_pass(
    pass_id: str, current_user: UserInDB = Depends(check_admin_user)
):
    result = await db.passes.update_one(
        {"_id": ObjectId(pass_id)}, {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Pass not found")
    return {"message": "Pass deactivated successfully"}

from fastapi import APIRouter, Depends
from typing import List, Optional

from controller.passes import (
    list_passes_controller,
    get_pass_controller,
    create_pass_controller,
    create_group_pass_controller,
    update_pass_controller,
    delete_pass_controller,
    deactivate_pass_controller,
    activate_pass_controller
)
from models.passes import PassCreate, PassUpdate, Pass
from models.user import UserInDB
from utils.security import check_admin_user

router = APIRouter()


@router.get("/", response_model=List[Pass])
async def list_passes():
    return await list_passes_controller()


@router.get("/{pass_id}", response_model=Pass)
async def get_pass(pass_id: str):
    return await get_pass_controller(pass_id)


@router.post("/")
async def create_pass(pass_: PassCreate, current_user: UserInDB = Depends(check_admin_user), zone_id: Optional[str] = None):
    return await create_pass_controller(pass_, zone_id)


@router.post("/group")
async def create_group_pass(pass_: PassCreate, current_user: UserInDB = Depends(check_admin_user), zone_id: Optional[str] = None):
    return await create_group_pass_controller(pass_, zone_id)


@router.put("/{pass_id}", response_model=Pass)
async def update_pass(pass_id: str, pass_update: PassUpdate, current_user: UserInDB = Depends(check_admin_user)):
    return await update_pass_controller(pass_id, pass_update)


@router.delete("/{pass_id}")
async def delete_pass(pass_id: str, current_user: UserInDB = Depends(check_admin_user)):
    return await delete_pass_controller(pass_id)


@router.put("/deactivate/{pass_id}")
async def deactivate_pass(pass_id: str, current_user: UserInDB = Depends(check_admin_user)):
    return await deactivate_pass_controller(pass_id)

@router.put("/activate/{pass_id}")
async def activate_pass(pass_id: str, current_user: UserInDB = Depends(check_admin_user)):
    return await activate_pass_controller(pass_id)

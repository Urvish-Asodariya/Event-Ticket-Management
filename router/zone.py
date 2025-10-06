from fastapi import APIRouter, Depends
from models.zone import ZoneCreate, ZoneUpdate, Zone
from models.user import UserInDB
from utils.security import check_admin_user
from controller.zone import (
    create_zone_controller,
    get_zone_controller,
    update_zone_controller,
    delete_zone_controller,
    deactivate_zone_controller
)

router = APIRouter()


@router.post("/", response_model=Zone)
async def create_zone(zone: ZoneCreate, current_admin: UserInDB = Depends(check_admin_user)):
    return await create_zone_controller(zone, current_admin)


@router.get("/{zone_id}", response_model=Zone)
async def get_zone(zone_id: str, current_admin: UserInDB = Depends(check_admin_user)):
    return await get_zone_controller(zone_id, current_admin)


@router.put("/{zone_id}", response_model=Zone)
async def update_zone(zone_id: str, zone: ZoneUpdate, current_admin: UserInDB = Depends(check_admin_user)):
    return await update_zone_controller(zone_id, zone)


@router.delete("/{zone_id}")
async def delete_zone(zone_id: str, current_admin: UserInDB = Depends(check_admin_user)):
    return await delete_zone_controller(zone_id)


@router.put("/deactivate/{zone_id}")
async def deactivate_zone(zone_id: str, current_admin: UserInDB = Depends(check_admin_user)):
    return await deactivate_zone_controller(zone_id)

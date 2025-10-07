from fastapi import APIRouter, status, Request, HTTPException, Depends
from models.zone import ZoneCreate, ZoneUpdate, Zone
from models.user import UserInDB
from utils.security import check_admin_user
from controller.zone import (
    create_zone_controller,
    get_zone_controller,
    update_zone_controller,
    delete_zone_controller,
    deactivate_zone_controller,
    activate_zone_controller,
    get_zone_stats_controller,
)

router = APIRouter()


@router.post("/", response_model=Zone)
async def create_zone(
    zone: ZoneCreate, current_admin: UserInDB = Depends(check_admin_user)
):
    try:
        return await create_zone_controller(zone, current_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{zone_id}", response_model=Zone)
async def get_zone(zone_id: str, current_admin: UserInDB = Depends(check_admin_user)):
    try:
        return await get_zone_controller(zone_id, current_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/{zone_id}", response_model=Zone)
async def update_zone(
    zone_id: str, zone: ZoneUpdate, current_admin: UserInDB = Depends(check_admin_user)
):
    try:
        return await update_zone_controller(zone_id, zone, current_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/{zone_id}")
async def delete_zone(
    zone_id: str, current_admin: UserInDB = Depends(check_admin_user)
):
    try:
        return await delete_zone_controller(zone_id, current_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/deactivate/{zone_id}")
async def deactivate_zone(
    zone_id: str, current_admin: UserInDB = Depends(check_admin_user)
):
    try:
        return await deactivate_zone_controller(zone_id, current_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/activate/{zone_id}")
async def activate_zone(
    zone_id: str, current_admin: UserInDB = Depends(check_admin_user)
):
    try:
        return await activate_zone_controller(zone_id, current_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/stats/{zone_id}")
async def get_zone_stats(
    zone_id: str, current_admin: UserInDB = Depends(check_admin_user)
):
    try:
        return await get_zone_stats_controller(zone_id, current_admin)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

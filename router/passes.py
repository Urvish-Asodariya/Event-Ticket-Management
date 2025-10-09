from fastapi import APIRouter, status, Request, HTTPException, Depends
from typing import List, Optional

from controller.passes import (
    list_passes_controller,
    get_pass_controller,
    create_pass_controller,
    create_group_pass_controller,
    update_pass_controller,
    delete_pass_controller,
    toggle_pass_controller
)
from models.passes import PassCreate, PassUpdate, Pass
from models.user import UserInDB
from utils.security import check_admin_user

router = APIRouter()


@router.get("/", response_model=List[Pass])
async def list_passes():
    try:
        return await list_passes_controller()
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{pass_id}", response_model=Pass)
async def get_pass(pass_id: str):
    try:
        return await get_pass_controller(pass_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/")
async def create_pass(
    pass_: PassCreate,
    current_user: UserInDB = Depends(check_admin_user),
    zone_id: Optional[str] = None,
):
    try:
        return await create_pass_controller(current_user, pass_, zone_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/group")
async def create_group_pass(
    pass_: PassCreate,
    current_user: UserInDB = Depends(check_admin_user),
    zone_id: Optional[str] = None,
):
    try:
        return await create_group_pass_controller(pass_, zone_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/{pass_id}", response_model=Pass)
async def update_pass(
    pass_id: str,
    pass_update: PassUpdate,
    current_user: UserInDB = Depends(check_admin_user),
):
    try:
        return await update_pass_controller(pass_id, pass_update, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/{pass_id}")
async def delete_pass(pass_id: str, current_user: UserInDB = Depends(check_admin_user)):
    try:
        return await delete_pass_controller(pass_id, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/toggle/{pass_id}")
async def toggle_pass(
    pass_id: str, current_user: UserInDB = Depends(check_admin_user)
):
    try:
        return await toggle_pass_controller(pass_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

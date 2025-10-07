from fastapi import APIRouter, status, Request, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from models.user import UserInDB
from models.zone import Zone
from models.booking import Booking
from models.discount import Discount, DiscountCreate
from utils.security import check_admin_user
from controller.admin import (
    list_users_controller,
    list_staffs_controller,
    list_zones_controller,
    get_staff_sales_report_controller,
    get_stats_controller,
    create_discount_controller,
    get_discounts_controller,
    get_group_bookings_controller,
    get_all_bookings_controller,
)

router = APIRouter()


# Users
@router.get("/users", response_model=List[UserInDB])
async def list_users(
    current_user: UserInDB = Depends(check_admin_user), skip: int = 0, limit: int = 100
):
    try:
        return await list_users_controller(skip, limit, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/staffs", response_model=List[UserInDB])
async def list_staffs(
    current_user: UserInDB = Depends(check_admin_user), skip: int = 0, limit: int = 100
):
    try:
        return await list_staffs_controller(skip, limit, current_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Zones
@router.get("/", response_model=List[Zone])
async def list_zones(current_admin: UserInDB = Depends(check_admin_user)):
    try:
        return await list_zones_controller()
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Staff Sales
@router.get("/staff-sales")
async def get_staff_sales_report(
    current_user: UserInDB = Depends(check_admin_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    try:
        return await get_staff_sales_report_controller(start_date, end_date)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Stats
@router.get("/stats")
async def get_stats(
    current_user: UserInDB = Depends(check_admin_user), period: str = "today"
):
    try:
        return await get_stats_controller(period)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Discounts
@router.post("/discounts", response_model=Discount)
async def create_discount(
    discount: DiscountCreate, current_user: UserInDB = Depends(check_admin_user)
):
    try:
        return await create_discount_controller(discount)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/discounts")
async def get_discounts(
    current_user: UserInDB = Depends(check_admin_user), zone_id: Optional[str] = None
):
    try:
        return await get_discounts_controller(zone_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Bookings
@router.get("/group-bookings")
async def get_group_bookings(
    current_user: UserInDB = Depends(check_admin_user), status: Optional[str] = None
):
    try:
        return await get_group_bookings_controller(status)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/bookings", response_model=List[Booking])
async def get_all_bookings(
    current_user: UserInDB = Depends(check_admin_user),
    zone_id: Optional[str] = None,
    status: Optional[str] = None,
):
    try:
        return await get_all_bookings_controller(zone_id, status)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected  error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

from fastapi import APIRouter, Depends, HTTPException, status
from utils.mongodb import db
from models.user import UserInDB
from models.booking import BookingStatus
from utils.security import get_current_user
from bson import ObjectId

router = APIRouter()



@router.post("/validate-qr")
async def validate_qr_code(
    qr_code: str,
    current_user: UserInDB = Depends(get_current_user)
):

    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    booking = await db["bookings"].find_one({"_id": ObjectId(qr_code)})
    if not booking:
        raise HTTPException(status_code=404, detail="Invalid QR code")

    if current_user.role == "staff":
        staff_zone = current_user.zone_id if hasattr(current_user, "zone_id") else None
        if not staff_zone:
            raise HTTPException(status_code=400, detail="Staff zone not assigned")
        if str(staff_zone) != str(booking.get("zone_id")):
            raise HTTPException(status_code=403, detail="Booking does not belong to your zone")

    if booking["status"] != "active":
        return {"valid": False, "message": f"Pass is {booking['status']}"}

    if booking.get("is_group", False):
        group_members = booking.get("group_members", [])
        available_entries = sum(1 for member in group_members if not member["entry_status"])
        if available_entries == 0:
            return {"valid": False, "message": "All group members already entered"}

        return {
            "valid": True,
            "is_group": True,
            "available_entries": available_entries,
            "group_members": [
                {
                    "name": m["name"],
                    "phone": m["phone"],
                    "entered": m["entry_status"],
                }
                for m in group_members
            ],
            "message": "Group booking validated, select member to mark entry."
        }

    await db["bookings"].update_one(
        {"_id": ObjectId(qr_code)},
        {"$set": {"status": BookingStatus.USED}}
    )

    return {
        "valid": True,
        "is_group": False,
        "message": "Entry validated successfully"
    }


@router.post("/validate-group-entry/{booking_id}/{member_index}")
async def validate_group_member_entry(
    booking_id: str,
    member_index: int,
    current_user: UserInDB = Depends(get_current_user)
):

    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})
    if not booking or not booking.get("is_group", False):
        raise HTTPException(status_code=404, detail="Invalid or non-group booking")

    if current_user.role == "staff":
        staff_zone = current_user.zone_id if hasattr(current_user, "zone_id") else None
        if not staff_zone:
            raise HTTPException(status_code=400, detail="Staff zone not assigned")
        if str(staff_zone) != str(booking.get("zone_id")):
            raise HTTPException(status_code=403, detail="Booking does not belong to your zone")

    if booking["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Booking is {booking['status']}")

    group_members = booking.get("group_members", [])
    if member_index >= len(group_members):
        raise HTTPException(status_code=400, detail="Invalid member index")

    if group_members[member_index]["entry_status"]:
        raise HTTPException(status_code=400, detail="Member already entered")

    update_path = f"group_members.{member_index}.entry_status"
    await db["bookings"].update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {update_path: True}}
    )

    group_members[member_index]["entry_status"] = True
    all_entered = all(m["entry_status"] for m in group_members)

    if all_entered:
        await db["bookings"].update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"status": BookingStatus.USED}}
        )

    return {
        "success": True,
        "message": "Member entry validated successfully",
        "all_entered": all_entered
    }
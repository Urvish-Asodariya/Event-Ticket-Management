from fastapi import HTTPException
from bson import ObjectId
from typing import Dict
from utils.mongodb import db
from utils.serializers import serialize_doc
from models.user import UserInDB
from models.booking import BookingStatus

async def validate_qr_controller(qr_code: str, current_user: UserInDB) -> Dict:
    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    booking = await db["bookings"].find_one({"_id": ObjectId(qr_code)})
    if not booking:
        raise HTTPException(status_code=404, detail="Invalid QR code")

    if current_user.role == "staff":
        staff_zone = getattr(current_user, "zone_id", None)
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


async def validate_group_member_entry_controller(booking_id: str, member_index: int, current_user: UserInDB) -> Dict:
    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})
    if not booking or not booking.get("is_group", False):
        raise HTTPException(status_code=404, detail="Invalid or non-group booking")

    if current_user.role == "staff":
        staff_zone = getattr(current_user, "zone_id", None)
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
    await db["bookings"].update_one({"_id": ObjectId(booking_id)}, {"$set": {update_path: True}})
    group_members[member_index]["entry_status"] = True

    all_entered = all(m["entry_status"] for m in group_members)
    if all_entered:
        await db["bookings"].update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": BookingStatus.USED}})

    return {
        "success": True,
        "message": "Member entry validated successfully",
        "all_entered": all_entered
    }

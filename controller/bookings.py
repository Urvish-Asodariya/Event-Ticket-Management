from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from utils.mongodb import db
from fastapi.responses import JSONResponse
from models.booking import BookingCreate, BookingInDB, Booking, BookingUpdate
from models.user import UserInDB
from utils.security import get_current_user
from utils.qr_service import generate_qr_code
from bson import ObjectId
import qrcode
import base64
from utils.serializers import serialize_doc, serialize_list
from datetime import datetime
from io import BytesIO
from utils.payment_service import PaymentService

payment_service = PaymentService()


async def create_booking_controller(
    pass_id: str,
    booking: BookingCreate,
    current_user: UserInDB = Depends(get_current_user),
):

    try:
        pass_ = await db["passes"].find_one({"_id": ObjectId(pass_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid pass ID format")

    if not pass_:
        raise HTTPException(status_code=404, detail="Pass not found")

    if not pass_.get("is_active", False):
        raise HTTPException(status_code=400, detail="Pass is inactive")

    now = datetime.utcnow()
    validity_end = pass_.get("validity_end")

    if validity_end and now > validity_end:
        raise HTTPException(status_code=400, detail="Pass validity has expired")

    group_size_allowed = pass_.get("group_size", 0)
    booking_is_group = group_size_allowed > 1

    quantity_requested = 1
    if booking_is_group:
        if not booking.group_members or len(booking.group_members) == 0:
            raise HTTPException(
                status_code=400,
                detail="Group members required for group booking",
            )
        quantity_requested = len(booking.group_members)
        if quantity_requested > group_size_allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Group size exceeds allowed limit ({group_size_allowed})",
            )
    else:
        if booking.group_members and len(booking.group_members) > 1:
            raise HTTPException(
                status_code=400,
                detail="Single pass cannot include multiple group members",
            )

    available_quantity = pass_.get("available_quantity", 0)
    if available_quantity < quantity_requested:
        raise HTTPException(
            status_code=400,
            detail=f"Only {available_quantity} passes are available",
        )

    amount = pass_["price"] * quantity_requested
    zone_id = str(pass_.get("zone_id"))

    if not getattr(booking, "discount_applied", None) and pass_.get("pricing_rules"):
        for rule in pass_["pricing_rules"]:
            valid_until = rule.get("valid_until")
            if valid_until and now <= valid_until:
                if rule.get("discount_percentage"):
                    amount -= amount * (rule["discount_percentage"] / 100)
                elif rule.get("fixed_price") and rule["fixed_price"] > 0:
                    amount = rule["fixed_price"] * quantity_requested

    if getattr(booking, "discount_applied", None):
        discount = await db["discounts"].find_one(
            {
                "$or": [
                    {"assigned_to": str(current_user["_id"])},
                    {"zone_id": zone_id},
                ],
                "is_active": True,
                "expiry": {"$gt": now},
            }
        )

        if not discount or discount["percentage"] < booking.discount_applied:
            raise HTTPException(
                status_code=403, detail="Invalid or unauthorized discount"
            )

        discount_value = amount * (booking.discount_applied / 100)
        if discount.get("max_limit") and discount_value > discount["max_limit"]:
            discount_value = discount["max_limit"]
        amount -= discount_value

        await db["discounts"].update_one(
            {"_id": discount["_id"]},
            {
                "$inc": {"times_used": 1},
                "$addToSet": {"used_by": str(current_user["_id"])},
            },
        )
    try:
        order_info = payment_service.create_razorpay_order(
            username=current_user["name"],
            email=current_user["email"],
            product=pass_["name"],
            amount=amount,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Unexpected payment error:", e)
        raise HTTPException(status_code=500, detail="Failed to create payment order")

    if order_info and order_info.get("order_id"):
        booking_dict = booking.dict(exclude={"is_group"})
        booking_dict["_id"] = ObjectId()
        booking_dict["is_group"] = booking_is_group
        booking_dict["user_id"] = str(current_user["_id"])
        booking_dict["pass_id"] = str(pass_id)
        booking_dict["zone_id"] = zone_id
        booking_dict["amount_paid"] = amount
        booking_dict["status"] = "pending_payment"
        booking_dict["razorpay_order_id"] = order_info["order_id"]
        booking_dict["created_at"] = datetime.utcnow()

        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(str(booking_dict["_id"]))
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            buffered = BytesIO()
            qr_img.save(buffered, format="PNG")
            booking_dict["qr_code"] = base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            print("Warning: QR generation failed:", e)
            booking_dict["qr_code"] = None

        booking_result = await db["bookings"].insert_one(booking_dict)
        await db["passes"].update_one(
            {"_id": ObjectId(pass_id)},
            {"$inc": {"available_quantity": -quantity_requested}},
        )

        if booking_result.inserted_id:
            return JSONResponse(
                {
                    "message": "Booking created successfully",
                    "order_id": order_info["order_id"],
                    "amount": order_info["amount"],
                    "currency": order_info["currency"],
                    "booking_id": str(booking_dict["_id"]),
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Booking creation failed")

    raise HTTPException(status_code=400, detail="Payment order generation failed")


async def get_booking_controller(
    booking_id: str, current_user: UserInDB = Depends(get_current_user)
):

    try:
        booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking ID format"
        )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if str(booking["user_id"]) != str(current_user.id) and current_user.role not in [
        "staff",
        "admin",
    ]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return serialize_doc(booking)


async def cancel_booking_controller(
    booking_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    try:
        booking = await db["bookings"].find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format",
        )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    user_id_str = str(current_user["_id"])
    if (
        str(booking.get("user_id")) != user_id_str
        and getattr(current_user, "role", None) != "admin"
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this booking"
        )

    if booking.get("status") != "active":
        raise HTTPException(
            status_code=400,
            detail="Only active bookings can be cancelled",
        )

    payment_status = booking.get("payment_status")
    payment_id = booking.get("payment_id")
    amount_paid = float(booking.get("amount_paid", 0.0))

    if booking.get("is_group"):
        quantity_to_restore = len(booking.get("group_members", []) or [])
        if quantity_to_restore == 0:
            quantity_to_restore = 1
    else:
        quantity_to_restore = 1

    if payment_status != "paid" or not payment_id or amount_paid <= 0:
        update_result = await db["bookings"].update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "status": "cancelled",
                    "refund_status": "none",
                    "refund_amount": 0,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        await db["passes"].update_one(
            {"_id": ObjectId(booking["pass_id"])},
            {"$inc": {"available_quantity": quantity_to_restore}},
        )

        if update_result.modified_count == 1:
            return JSONResponse({"message": "Booking cancelled (no payment to refund)"})
        else:
            raise HTTPException(status_code=500, detail="Booking cancellation failed")

    try:
        notes = {
            "booking_id": str(booking_id),
            "user_id": str(booking.get("user_id")),
        }

        refund_resp = await payment_service.create_razorpay_refund(
            payment_id=payment_id,
            amount_float=amount_paid,
            notes=notes,
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refund attempt failed: {str(e)}")

    if refund_resp and refund_resp.get("id"):
        refund_id = refund_resp["id"]
        refund_status = refund_resp.get("status", "processed")
        refunded_amount_paise = refund_resp.get("amount", int(round(amount_paid * 100)))
        refunded_amount = refunded_amount_paise / 100.0

        update_fields = {
            "status": "cancelled",
            "refund_status": refund_status,
            "refund_amount": refunded_amount,
            "refund_id": refund_id,
            "updated_at": datetime.utcnow(),
        }

        result = await db["bookings"].update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": update_fields},
        )

        await db["passes"].update_one(
            {"_id": ObjectId(booking["pass_id"])},
            {"$inc": {"available_quantity": quantity_to_restore}},
        )

        if result.modified_count == 1:
            return JSONResponse(
                {
                    "message": "Booking cancelled and refunded successfully",
                    "refund_id": refund_id,
                    "refund_status": refund_status,
                    "refund_amount": refunded_amount,
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Refund processed but failed to update booking record. Please contact support.",
            )
    raise HTTPException(status_code=502, detail="Refund failed with payment gateway")


async def get_user_bookings_controller(
    user_id: str, current_user: UserInDB = Depends(get_current_user)
):
    # Check if user is requesting their own bookings or is staff/admin
    if user_id != str(current_user.id) and current_user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    bookings = await db["bookings"].find({"user_id": user_id}).to_list(None)

    return serialize_list(bookings)


async def get_user_own_bookings_controller(
    current_user: UserInDB = Depends(get_current_user),
):
    user_id = str(current_user.id)
    bookings = await db["bookings"].find({"user_id": user_id}).to_list(None)

    return serialize_list(bookings)
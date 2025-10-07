from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CASH = "cash"
    FAILED = "failed"

class BookingStatus(str, Enum):
    ACTIVE = "active"
    USED = "used"
    CANCELLED = "cancelled"

class RefundStatus(str, Enum):
    NONE = "none"
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"

class GroupMember(BaseModel):
    name: str
    phone: str
    entry_status: bool = False

class BookingCreate(BaseModel):
    group_members: Optional[List[GroupMember]] = None

class BookingInDB(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    pass_id: str
    zone_id: str
    qr_code: str
    group_qr_codes: Optional[List[str]] = None
    is_group: bool = False
    group_members: Optional[List[GroupMember]] = None
    status: BookingStatus = BookingStatus.ACTIVE
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_id: Optional[str] = None
    amount_paid: float = 0
    discount_applied: Optional[float] = None
    refund_status: RefundStatus = RefundStatus.NONE
    refund_amount: float = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BookingUpdate(BaseModel):
    payment_status: Optional[PaymentStatus] = None
    status: Optional[BookingStatus] = None
    group_members: Optional[List[GroupMember]] = None

class Booking(BaseModel):
    id: str = Field(..., alias="_id")
    qr_code: str
    is_group: bool
    amount_paid: float
    discount_applied: Optional[float] = None
    status: BookingStatus
    payment_status: PaymentStatus
    created_at: datetime
    group_members: Optional[List[GroupMember]] = None

class QRValidationResponse(BaseModel):
    valid: bool
    booking_id: Optional[str] = None
    message: Optional[str] = None
    group_members_status: Optional[List[GroupMember]] = None

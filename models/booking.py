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

class GroupMember(BaseModel):
    name: str
    phone: str
    entry_status: bool = False

class BookingBase(BaseModel):
    user_id: str
    pass_id: str
    zone_id: str
    is_group: bool = False
    group_members: Optional[List[GroupMember]] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    discount_applied: Optional[float] = None
    sold_by: Optional[str] = None  

class BookingCreate(BookingBase):
    pass

class RefundStatus(str, Enum):
    NONE = "none"
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"

class BookingInDB(BookingBase):
    id: str = Field(..., alias="_id")
    qr_code: str 
    group_qr_codes: Optional[List[str]] = None 
    status: BookingStatus = BookingStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    payment_id: Optional[str] = None
    amount_paid: float = 0
    refund_status: RefundStatus = RefundStatus.NONE
    refund_amount: float = 0

class BookingUpdate(BaseModel):
    payment_status: Optional[PaymentStatus] = None
    status: Optional[BookingStatus] = None
    group_members: Optional[List[GroupMember]] = None

class Booking(BookingBase):
    id: str = Field(..., alias="_id")
    qr_code: str
    status: BookingStatus
    created_at: datetime
    payment_id: Optional[str]
    amount_paid: float

class QRValidationResponse(BaseModel):
    valid: bool
    booking_id: Optional[str] = None
    message: Optional[str] = None
    group_members_status: Optional[List[GroupMember]] = None
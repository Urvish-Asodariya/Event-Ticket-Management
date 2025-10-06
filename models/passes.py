from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PassType(str, Enum):
    DAILY = "daily"
    SEASONAL = "seasonal"
    VIP = "vip"
    GROUP = "group"
    STUDENT = "student"

class PricingRule(BaseModel):
    condition: str 
    discount_percentage: Optional[float] = None
    fixed_price: Optional[float] = None
    valid_until: Optional[datetime] = None
    days: Optional[List[str]] = None 

class PassBase(BaseModel):
    name: str
    type: PassType
    price: float
    validity_start: datetime
    validity_end: datetime
    max_entries: int = 1
    group_size: Optional[int] = None
    description: Optional[str] = None
    early_bird_end: Optional[datetime] = None
    available_quantity: Optional[int] = None
    pricing_rules: Optional[List[PricingRule]] = None
    zone_id: Optional[str] = None 

class PassCreate(PassBase):
    created_by: str
    zone_id: str

class PassInDB(PassBase):
    id: str = Field(..., alias="_id")
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

class PassUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    validity_end: Optional[datetime] = None
    max_entries: Optional[int] = None
    is_active: Optional[bool] = None

class Pass(PassBase):
    id: str = Field(..., alias="_id")
    created_by: str
    created_at: datetime
    is_active: bool

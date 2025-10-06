from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ZoneBase(BaseModel):
    name: str
    description: Optional[str] = None

class ZoneCreate(ZoneBase):
    name: str
    description: Optional[str] = None
    created_by: Optional[str] = None

class ZoneInDB(ZoneBase):
    id: str = Field(..., alias="_id")
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Zone(ZoneInDB):
    pass

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


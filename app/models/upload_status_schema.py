from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UploadStatusBase(BaseModel):
    salesforce_id: str
    gclid: Optional[str] = None
    original_lead_created_datetime: datetime
    admission_date: datetime
    status: str
    error_details: Optional[str] = None

class UploadStatusCreate(UploadStatusBase):
    pass

class UploadStatusRead(UploadStatusBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

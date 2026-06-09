from pydantic import BaseModel
from typing import Optional

class AppVersionCreate(BaseModel):
    platform: str = "android"
    latest_version: str
    force_update: bool = False
    update_url: Optional[str] = None
    release_notes: Optional[str] = None

class AppVersionResponse(BaseModel):
    latest_version: str
    force_update: bool
    update_url: str
    release_notes: str

    class Config:
        from_attributes = True

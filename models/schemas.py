from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

from config import ItemCategory, SecondaryTag, GenerateMode, APIProvider


class ItemInfo(BaseModel):
    category: ItemCategory
    secondary_tags: List[SecondaryTag] = []
    user_description: Optional[str] = None


class GenerationRequest(BaseModel):
    item_info: ItemInfo
    mode: GenerateMode
    input_type: str
    input_data: str
    user_api_keys: Optional[dict] = None


class GenerationResponse(BaseModel):
    task_id: str
    status: str
    model_url: Optional[str] = None
    preview_url: Optional[str] = None
    provider: APIProvider
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class APIKeyInfo(BaseModel):
    provider: APIProvider
    key_name: str
    is_configured: bool
    description: str


class HistoryFilter(BaseModel):
    category: Optional[ItemCategory] = None
    provider: Optional[APIProvider] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[str] = None
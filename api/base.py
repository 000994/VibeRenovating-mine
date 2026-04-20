from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel
import httpx
import asyncio
from datetime import datetime


class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationResult(BaseModel):
    task_id: str
    status: GenerationStatus
    job_id: Optional[str] = None
    model_url: Optional[str] = None
    model_data: Optional[bytes] = None
    preview_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class BaseAPI(ABC):
    provider_name: str
    supports_text: bool = False
    supports_image: bool = True
    supports_preview: bool = True
    
    def __init__(self, api_key: str, secret_key: str = None, **kwargs):
        self.api_key = api_key
        self.secret_key = secret_key
        self.kwargs = kwargs
        trust_env = bool(kwargs.get("trust_env", False))
        retries = int(kwargs.get("connect_retries", 2))
        transport = httpx.AsyncHTTPTransport(
            trust_env=trust_env,
            retries=max(0, retries),
        )
        self._client = httpx.AsyncClient(
            timeout=300.0,
            trust_env=trust_env,
            transport=transport,
        )
    
    async def close(self):
        await self._client.aclose()
    
    @abstractmethod
    async def generate_from_image(
        self,
        image_data: bytes,
        filename: str = "image.png",
        task_id: str = None,
        **kwargs
    ) -> GenerationResult:
        pass
    
    @abstractmethod
    async def generate_from_text(
        self,
        text: str,
        task_id: str = None,
        **kwargs
    ) -> GenerationResult:
        pass
    
    @abstractmethod
    async def get_status(self, task_id: str) -> GenerationResult:
        pass
    
    @abstractmethod
    async def get_model_url(self, task_id: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def get_preview_url(self, task_id: str) -> Optional[str]:
        pass
    
    async def poll_until_complete(
        self,
        task_id: str,
        interval: float = 5.0,
        max_wait: float = 600.0,
    ) -> GenerationResult:
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < max_wait:
            result = await self.get_status(task_id)
            if result.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED]:
                return result
            await asyncio.sleep(interval)
        return GenerationResult(
            task_id=task_id,
            status=GenerationStatus.FAILED,
            error_message="Generation timed out",
        )
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def _download_file(self, url: str) -> bytes:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

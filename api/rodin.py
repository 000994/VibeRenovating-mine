import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
import hashlib
import time

from .base import BaseAPI, GenerationResult, GenerationStatus


class RodinAPI(BaseAPI):
    provider_name = "rodin"
    supports_text = False
    supports_image = True
    supports_preview = True
    
    BASE_URL = "https://api.hyperhuman.deemos.com/v2"
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self._task_cache: Dict[str, Dict] = {}
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def generate_from_image(
        self,
        image_data: bytes,
        filename: str = "image.png",
        task_id: str = None,
        **kwargs
    ) -> GenerationResult:
        task_id = task_id or str(uuid.uuid4())
        
        try:
            image_base64 = self._encode_image(image_data)
            
            payload = {
                "image": image_base64,
                "format": kwargs.get("format", "glb"),
                "quality": kwargs.get("quality", "high"),
            }
            
            response = await self._client.post(
                f"{self.BASE_URL}/generate",
                headers=self._get_headers(),
                json=payload,
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                rodin_task_id = result.get("task_id") or result.get("id")
                self._task_cache[task_id] = {
                    "rodin_task_id": rodin_task_id,
                    "created_at": datetime.utcnow(),
                }
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.PROCESSING,
                )
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.FAILED,
                    error_message=error_data.get("message", f"API error: {response.status_code}"),
                )
        except Exception as e:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=str(e),
            )
    
    async def generate_from_text(
        self,
        text: str,
        task_id: str = None,
        **kwargs
    ) -> GenerationResult:
        return GenerationResult(
            task_id=task_id or str(uuid.uuid4()),
            status=GenerationStatus.FAILED,
            error_message="Rodin does not support text-to-3D generation",
        )
    
    async def get_status(self, task_id: str) -> GenerationResult:
        cache = self._task_cache.get(task_id)
        if not cache:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="Task not found",
            )
        
        rodin_task_id = cache.get("rodin_task_id")
        
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/task/{rodin_task_id}",
                headers=self._get_headers(),
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "").lower()
                
                if status in ["completed", "success", "succeeded"]:
                    return GenerationResult(
                        task_id=task_id,
                        status=GenerationStatus.COMPLETED,
                        model_url=result.get("model_url") or result.get("download_url"),
                        preview_url=result.get("preview_url") or result.get("thumbnail_url"),
                    )
                elif status in ["failed", "error"]:
                    return GenerationResult(
                        task_id=task_id,
                        status=GenerationStatus.FAILED,
                        error_message=result.get("error", "Unknown error"),
                    )
                else:
                    return GenerationResult(
                        task_id=task_id,
                        status=GenerationStatus.PROCESSING,
                    )
            else:
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.FAILED,
                    error_message=f"Status check failed: {response.status_code}",
                )
        except Exception as e:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=str(e),
            )
    
    async def get_model_url(self, task_id: str) -> Optional[str]:
        result = await self.get_status(task_id)
        return result.model_url
    
    def get_preview_url(self, task_id: str) -> Optional[str]:
        cache = self._task_cache.get(task_id)
        return cache.get("preview_url") if cache else None
    
    def _encode_image(self, image_data: bytes) -> str:
        import base64
        return base64.b64encode(image_data).decode("utf-8")
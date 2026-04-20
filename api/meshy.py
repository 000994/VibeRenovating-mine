import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

from .base import BaseAPI, GenerationResult, GenerationStatus


class MeshyAPI(BaseAPI):
    provider_name = "meshy"
    supports_text = True
    supports_image = True
    supports_preview = True
    
    BASE_URL = "https://api.meshy.ai/v2"
    
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
                "mode": "preview",
                "input": {
                    "image_url": f"data:image/png;base64,{image_base64}",
                },
                "art_style": kwargs.get("art_style", "realistic"),
                "texture_richness": kwargs.get("texture_richness", "high"),
            }
            
            response = await self._client.post(
                f"{self.BASE_URL}/image-to-3d",
                headers=self._get_headers(),
                json=payload,
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                meshy_task_id = result.get("result")
                self._task_cache[task_id] = {
                    "meshy_task_id": meshy_task_id,
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
                    error_message=error_data.get("error", {}).get("message", f"API error: {response.status_code}"),
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
        task_id = task_id or str(uuid.uuid4())
        
        try:
            payload = {
                "mode": "preview",
                "input": {
                    "text": text,
                },
                "art_style": kwargs.get("art_style", "realistic"),
                "texture_richness": kwargs.get("texture_richness", "high"),
            }
            
            response = await self._client.post(
                f"{self.BASE_URL}/text-to-3d",
                headers=self._get_headers(),
                json=payload,
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                meshy_task_id = result.get("result")
                self._task_cache[task_id] = {
                    "meshy_task_id": meshy_task_id,
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
                    error_message=error_data.get("error", {}).get("message", f"API error: {response.status_code}"),
                )
        except Exception as e:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=str(e),
            )
    
    async def refine_model(self, task_id: str, **kwargs) -> GenerationResult:
        cache = self._task_cache.get(task_id)
        if not cache:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="Task not found",
            )
        
        meshy_task_id = cache.get("meshy_task_id")
        try:
            response = await self._client.post(
                f"{self.BASE_URL}/image-to-3d/{meshy_task_id}/refine",
                headers=self._get_headers(),
            )
            
            if response.status_code == 200:
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.PROCESSING,
                )
            else:
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.FAILED,
                    error_message=f"Refine failed: {response.status_code}",
                )
        except Exception as e:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=str(e),
            )
    
    async def get_status(self, task_id: str) -> GenerationResult:
        cache = self._task_cache.get(task_id)
        if not cache:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="Task not found",
            )
        
        meshy_task_id = cache.get("meshy_task_id")
        
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/image-to-3d/{meshy_task_id}",
                headers=self._get_headers(),
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                
                if status == "SUCCEEDED":
                    return GenerationResult(
                        task_id=task_id,
                        status=GenerationStatus.COMPLETED,
                        model_url=result.get("model_urls", {}).get("glb"),
                        preview_url=result.get("thumbnail_url"),
                    )
                elif status == "FAILED":
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
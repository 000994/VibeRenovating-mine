import uuid
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from config import ItemCategory, SecondaryTag, GenerateMode, APIProvider
from api import (
    BaseAPI, SF3DAPI, MeshyAPI, RodinAPI, HunyuanAPI, TripoAPI,
    GenerationResult, GenerationStatus,
)
from core.router import route_api, get_recommended_apis, get_api_description
from models.database import Database, GenerationRecord
from utils.storage import StorageManager


@dataclass
class GenerationTask:
    task_id: str
    category: ItemCategory
    secondary_tags: List[SecondaryTag]
    mode: GenerateMode
    provider: APIProvider
    input_type: str
    input_data: str
    input_file_path: Optional[str] = None
    status: str = "pending"
    job_id: Optional[str] = None
    model_url: Optional[str] = None
    preview_url: Optional[str] = None
    model_file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class Generator:
    def __init__(
        self,
        db: Database = None,
        storage: StorageManager = None,
    ):
        self.db = db or Database()
        self.storage = storage or StorageManager()
        self._api_clients: Dict[APIProvider, BaseAPI] = {}
    
    def get_api_client(
        self,
        provider: APIProvider,
        api_key: str,
        secret_key: str = None,
    ) -> BaseAPI:
        cache_key = (provider, api_key, secret_key)
        if cache_key not in self._api_clients:
            if provider == APIProvider.SF3D:
                self._api_clients[cache_key] = SF3DAPI(api_key)
            elif provider == APIProvider.MESHY:
                self._api_clients[cache_key] = MeshyAPI(api_key)
            elif provider == APIProvider.RODIN:
                self._api_clients[cache_key] = RodinAPI(api_key)
            elif provider == APIProvider.HUNYUAN:
                self._api_clients[cache_key] = HunyuanAPI(api_key, secret_key=secret_key)
            elif provider == APIProvider.TRIPO:
                self._api_clients[cache_key] = TripoAPI(api_key)
        return self._api_clients[cache_key]
    
    def create_task(
        self,
        category: ItemCategory,
        secondary_tags: List[SecondaryTag],
        mode: GenerateMode,
        input_type: str,
        input_data: str,
        provider: APIProvider = None,
        available_providers: List[APIProvider] = None,
        api_keys: Dict[APIProvider, Dict] = None,
    ) -> GenerationTask:
        task_id = str(uuid.uuid4())
        
        if provider is None:
            provider = route_api(category, secondary_tags, mode, available_providers)
        
        input_file_path = None
        if input_type == "image" and input_data.startswith("/"):
            input_file_path = input_data
        
        task = GenerationTask(
            task_id=task_id,
            category=category,
            secondary_tags=secondary_tags,
            mode=mode,
            provider=provider,
            input_type=input_type,
            input_data=input_data,
            input_file_path=input_file_path,
        )
        
        self.db.create_record(
            task_id=task_id,
            category=category.value,
            secondary_tags=[t.value for t in secondary_tags],
            mode=mode.value,
            input_type=input_type,
            input_data=input_data if input_type == "text" else "",
            provider=provider.value,
            input_file_path=input_file_path,
        )
        
        return task
    
    async def execute_task(
        self,
        task: GenerationTask,
        api_keys: Dict[APIProvider, Dict],
        generation_options: Dict[str, Any] = None,
    ) -> GenerationResult:
        generation_options = generation_options or {}
        key_info = api_keys.get(task.provider)
        if not key_info:
            return GenerationResult(
                task_id=task.task_id,
                status=GenerationStatus.FAILED,
                error_message=f"No API key for {task.provider.value}",
            )
        
        api_client = self.get_api_client(
            task.provider,
            key_info.get("api_key"),
            key_info.get("secret_key"),
        )
        
        try:
            if task.input_type == "image":
                image_data = await self._get_image_data(task.input_data, task.input_file_path)
                result = await api_client.generate_from_image(
                    image_data=image_data,
                    filename=task.input_file_path.split("/")[-1] if task.input_file_path else "image.png",
                    task_id=task.task_id,
                    **generation_options,
                )
            else:
                result = await api_client.generate_from_text(
                    text=task.input_data,
                    task_id=task.task_id,
                    **generation_options,
                )
            
            if result.job_id:
                self.db.update_record(task_id=task.task_id, job_id=result.job_id)
            
            if result.status == GenerationStatus.PROCESSING:
                result = await api_client.poll_until_complete(task.task_id)
                result = GenerationResult(
                    task_id=task.task_id,
                    status=result.status,
                    job_id=result.job_id,
                    model_url=result.model_url,
                    preview_url=result.preview_url,
                    error_message=result.error_message,
                )
            
            self.db.update_record(
                task_id=task.task_id,
                status=result.status.value,
                model_url=result.model_url,
                preview_url=result.preview_url,
                error_message=result.error_message,
            )
            
            if result.status == GenerationStatus.COMPLETED:
                if result.model_data:
                    model_path = self.storage.save_model(result.model_data, task.task_id)
                    self.db.update_record(task_id=task.task_id, model_file_path=model_path)
                elif result.model_url:
                    model_path = await self._save_model(result.model_url, task.task_id)
                    self.db.update_record(task_id=task.task_id, model_file_path=model_path)
                await self._cache_preview(result.preview_url, task.task_id)
            
            return result
        except Exception as e:
            error_message = str(e)
            if "All connection attempts failed" in error_message:
                error_message = (
                    "All connection attempts failed. "
                    "请检查当前网络是否可访问外网 API，或关闭错误代理后重试。"
                )
            self.db.update_record(
                task_id=task.task_id,
                status=GenerationStatus.FAILED.value,
                error_message=error_message,
            )
            return GenerationResult(
                task_id=task.task_id,
                status=GenerationStatus.FAILED,
                error_message=error_message,
            )
    
    async def poll_task(self, task: GenerationTask, api_keys: Dict[APIProvider, Dict]) -> GenerationResult:
        key_info = api_keys.get(task.provider)
        if not key_info:
            return GenerationResult(
                task_id=task.task_id,
                status=GenerationStatus.FAILED,
                error_message=f"No API key for {task.provider.value}",
            )
        
        api_client = self.get_api_client(
            task.provider,
            key_info.get("api_key"),
            key_info.get("secret_key"),
        )
        
        result = await api_client.poll_until_complete(task.task_id)
        
        self.db.update_record(
            task_id=task.task_id,
            status=result.status.value,
            model_url=result.model_url,
            preview_url=result.preview_url,
            error_message=result.error_message,
        )
        
        if result.status == GenerationStatus.COMPLETED:
            if result.model_data:
                model_path = self.storage.save_model(result.model_data, task.task_id)
                self.db.update_record(task_id=task.task_id, model_file_path=model_path)
            elif result.model_url:
                model_path = await self._save_model(result.model_url, task.task_id)
                self.db.update_record(task_id=task.task_id, model_file_path=model_path)
            await self._cache_preview(result.preview_url, task.task_id)
        
        return result
    
    async def _get_image_data(self, input_data: str, file_path: str = None) -> bytes:
        if file_path:
            with open(file_path, "rb") as f:
                return f.read()
        if input_data.startswith("data:image"):
            import base64
            base64_data = input_data.split(",")[1]
            return base64.b64decode(base64_data)
        if input_data.startswith("http"):
            async with asyncio.get_event_loop() as loop:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(input_data)
                    return response.content
        import base64
        return base64.b64decode(input_data)
    
    async def _save_model(self, model_url: str, task_id: str) -> str:
        model_data = await self._download_model(model_url)
        return self.storage.save_model(model_data, task_id)
    
    async def _download_model(self, url: str) -> bytes:
        import httpx
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def _cache_preview(self, preview_url: Optional[str], task_id: str) -> None:
        if not preview_url:
            return
        if self.storage.get_preview_path(task_id):
            return

        import httpx
        try:
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                response = await client.get(preview_url)
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                self.storage.save_preview(
                    response.content,
                    task_id=task_id,
                    source_url=preview_url,
                    content_type=content_type,
                )
        except Exception:
            # Ignore preview cache failures to avoid impacting main generation flow.
            return
    
    def get_task(self, task_id: str) -> Optional[GenerationTask]:
        record = self.db.get_record(task_id)
        if record:
            return self._record_to_task(record)
        return None
    
    def get_tasks(
        self,
        category: ItemCategory = None,
        provider: APIProvider = None,
        status: str = None,
        limit: int = 50,
    ) -> List[GenerationTask]:
        records = self.db.get_records(
            category=category.value if category else None,
            provider=provider.value if provider else None,
            status=status,
            limit=limit,
        )
        return [self._record_to_task(r) for r in records]
    
    def _record_to_task(self, record: GenerationRecord) -> GenerationTask:
        return GenerationTask(
            task_id=record.task_id,
            category=ItemCategory(record.category),
            secondary_tags=[SecondaryTag(t) for t in record.get_secondary_tags()],
            mode=GenerateMode(record.mode),
            provider=APIProvider(record.provider),
            input_type=record.input_type,
            input_data=record.input_data,
            input_file_path=record.input_file_path,
            status=record.status,
            job_id=record.job_id,
            model_url=record.model_url,
            preview_url=record.preview_url,
            model_file_path=record.model_file_path,
            error_message=record.error_message,
            created_at=record.created_at,
            completed_at=record.completed_at,
        )
    
    def delete_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task:
            if task.model_file_path:
                self.storage.delete_file(task.model_file_path)
            if task.input_file_path:
                self.storage.delete_file(task.input_file_path)
            return self.db.delete_record(task_id)
        return False

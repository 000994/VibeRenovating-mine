import os
import uuid
from typing import Optional
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from config import settings


class StorageManager:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir = self.output_dir / "models"
        self.models_dir.mkdir(exist_ok=True)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
    
    def save_model(self, model_data: bytes, task_id: str, format: str = "glb") -> str:
        filename = f"{task_id}.{format}"
        filepath = self.models_dir / filename
        with open(filepath, "wb") as f:
            f.write(model_data)
        return str(filepath)
    
    def save_image(self, image_data: bytes, task_id: str = None, filename: str = None) -> str:
        if task_id is None:
            task_id = str(uuid.uuid4())
        if filename is None:
            filename = f"{task_id}.png"
        filepath = self.images_dir / filename
        with open(filepath, "wb") as f:
            f.write(image_data)
        return str(filepath)

    def save_preview(
        self,
        preview_data: bytes,
        task_id: str,
        source_url: str = "",
        content_type: str = "",
    ) -> str:
        ext = self._detect_preview_ext(source_url=source_url, content_type=content_type)
        filename = f"{task_id}_preview{ext}"
        filepath = self.images_dir / filename
        with open(filepath, "wb") as f:
            f.write(preview_data)
        return str(filepath)
    
    def get_model_path(self, task_id: str, format: str = "glb") -> Optional[str]:
        filepath = self.models_dir / f"{task_id}.{format}"
        if filepath.exists():
            return str(filepath)
        return None
    
    def get_image_path(self, filename: str) -> Optional[str]:
        filepath = self.images_dir / filename
        if filepath.exists():
            return str(filepath)
        return None

    def get_preview_path(self, task_id: str) -> Optional[str]:
        for candidate in self.images_dir.glob(f"{task_id}_preview.*"):
            if candidate.exists():
                return str(candidate)
        return None
    
    def delete_file(self, filepath: str) -> bool:
        path = Path(filepath)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def get_model_url(self, task_id: str) -> Optional[str]:
        path = self.get_model_path(task_id)
        if path:
            return f"/models/{task_id}.glb"
        return None
    
    def list_models(self) -> list:
        return [str(f) for f in self.models_dir.glob("*.glb")]
    
    def list_images(self) -> list:
        return [str(f) for f in self.images_dir.glob("*.*")]
    
    def get_storage_stats(self) -> dict:
        models = list(self.models_dir.glob("*.*"))
        images = list(self.images_dir.glob("*.*"))
        models_size = sum(f.stat().st_size for f in models)
        images_size = sum(f.stat().st_size for f in images)
        return {
            "models_count": len(models),
            "images_count": len(images),
            "models_size_mb": models_size / (1024 * 1024),
            "images_size_mb": images_size / (1024 * 1024),
            "total_size_mb": (models_size + images_size) / (1024 * 1024),
        }

    def _detect_preview_ext(self, source_url: str, content_type: str) -> str:
        ct = (content_type or "").lower()
        if "video/mp4" in ct:
            return ".mp4"
        if "image/webp" in ct:
            return ".webp"
        if "image/jpeg" in ct:
            return ".jpg"
        if "image/png" in ct:
            return ".png"

        path = urlparse(source_url or "").path.lower()
        for ext in [".mp4", ".webm", ".png", ".jpg", ".jpeg", ".webp"]:
            if path.endswith(ext):
                return ext
        return ".png"

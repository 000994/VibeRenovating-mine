import uuid
from typing import Optional, Dict, Any
from pathlib import Path

from .base import BaseAPI, GenerationResult, GenerationStatus


class SF3DAPI(BaseAPI):
    provider_name = "sf3d"
    supports_text = False
    supports_image = True
    supports_preview = True

    ENDPOINT = "https://api.stability.ai/v2beta/3d/stable-fast-3d"

    @staticmethod
    def _guess_mime_type(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if ext == ".webp":
            return "image/webp"
        return "image/png"

    @staticmethod
    def _normalize_options(options: Dict[str, Any]) -> Dict[str, Any]:
        texture_resolution = int(options.get("texture_resolution", 1024))
        if texture_resolution not in {512, 1024, 2048}:
            texture_resolution = 1024

        foreground_ratio = float(options.get("foreground_ratio", 0.85))
        if foreground_ratio < 0.1 or foreground_ratio > 1.0:
            foreground_ratio = 0.85

        remesh = str(options.get("remesh", "none")).lower()
        if remesh not in {"none", "triangle", "quad"}:
            remesh = "none"

        vertex_count = int(options.get("vertex_count", -1))
        if vertex_count < -1 or vertex_count > 20000:
            vertex_count = -1

        payload = {
            "texture_resolution": str(texture_resolution),
            "foreground_ratio": foreground_ratio,
            "remesh": remesh,
        }
        if vertex_count != -1:
            payload["vertex_count"] = vertex_count
        return payload

    @staticmethod
    def _extract_error_message(response) -> str:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                data = response.json()
                if isinstance(data, dict):
                    errors = data.get("errors")
                    if errors:
                        return str(errors)
                    if data.get("message"):
                        return str(data["message"])
            except Exception:
                pass
        return f"SF3D API error: {response.status_code}"

    async def generate_from_image(
        self,
        image_data: bytes,
        filename: str = "image.png",
        task_id: str = None,
        **kwargs,
    ) -> GenerationResult:
        task_id = task_id or str(uuid.uuid4())

        try:
            headers: Dict[str, str] = {
                "Authorization": f"Bearer {self.api_key}",
            }

            # Optional telemetry headers supported by Stability.
            for source_key, header_key in [
                ("stability_client_id", "stability-client-id"),
                ("stability_client_user_id", "stability-client-user-id"),
                ("stability_client_version", "stability-client-version"),
            ]:
                value = kwargs.get(source_key)
                if value:
                    headers[header_key] = str(value)[:256]

            files = {
                "image": (filename, image_data, self._guess_mime_type(filename)),
            }
            data = self._normalize_options(kwargs)

            response = await self._client.post(
                self.ENDPOINT,
                headers=headers,
                files=files,
                data=data,
            )

            if response.status_code == 200:
                if not response.content:
                    return GenerationResult(
                        task_id=task_id,
                        status=GenerationStatus.FAILED,
                        error_message="SF3D returned empty model content",
                    )
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.COMPLETED,
                    model_data=response.content,
                )

            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=self._extract_error_message(response),
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
        **kwargs,
    ) -> GenerationResult:
        return GenerationResult(
            task_id=task_id or str(uuid.uuid4()),
            status=GenerationStatus.FAILED,
            error_message="SF3D does not support text-to-3D generation",
        )

    async def get_status(self, task_id: str) -> GenerationResult:
        # SF3D is synchronous from this endpoint; generate_from_image returns final result.
        return GenerationResult(task_id=task_id, status=GenerationStatus.COMPLETED)

    async def get_model_url(self, task_id: str) -> Optional[str]:
        return None

    def get_preview_url(self, task_id: str) -> Optional[str]:
        return None

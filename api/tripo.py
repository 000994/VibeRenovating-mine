import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from .base import BaseAPI, GenerationResult, GenerationStatus


class TripoAPI(BaseAPI):
    provider_name = "tripo"
    supports_text = True
    supports_image = True
    supports_preview = True

    BASE_URL = "https://api.tripo3d.ai/v2/openapi"
    DEFAULT_MODEL_VERSION = "v2.5-20250123"

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
        **kwargs,
    ) -> GenerationResult:
        task_id = task_id or str(uuid.uuid4())

        try:
            image_token = await self._upload_image(image_data, filename)
            if not image_token:
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.FAILED,
                    error_message="Failed to upload image to Tripo.",
                )

            payload: Dict[str, Any] = {
                "type": "image_to_model",
                "file": {
                    "type": self._guess_file_type(filename),
                    "file_token": image_token,
                },
            }
            self._merge_generation_options(payload, kwargs, text_mode=False)

            response = await self._client.post(
                f"{self.BASE_URL}/task",
                headers=self._get_headers(),
                json=payload,
            )

            return self._handle_submit_response(response, task_id)
        except Exception as exc:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=str(exc),
            )

    async def generate_from_text(
        self,
        text: str,
        task_id: str = None,
        **kwargs,
    ) -> GenerationResult:
        task_id = task_id or str(uuid.uuid4())

        try:
            payload: Dict[str, Any] = {
                "type": "text_to_model",
                "prompt": text,
            }
            self._merge_generation_options(payload, kwargs, text_mode=True)

            response = await self._client.post(
                f"{self.BASE_URL}/task",
                headers=self._get_headers(),
                json=payload,
            )

            return self._handle_submit_response(response, task_id)
        except Exception as exc:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=str(exc),
            )

    async def get_status(self, task_id: str) -> GenerationResult:
        cache = self._task_cache.get(task_id)
        if not cache:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="Task not found",
            )

        tripo_task_id = cache.get("tripo_task_id")
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/task/{tripo_task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )

            if response.status_code != 200:
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.FAILED,
                    error_message=f"Status check failed: HTTP {response.status_code}",
                )

            body = response.json()
            if body.get("code") not in (0, None):
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.FAILED,
                    error_message=self._extract_error(body),
                )

            data = body.get("data", body)
            status = str(data.get("status", "")).lower()

            if status in {"success", "completed", "succeeded", "done"}:
                model_url, preview_url = self._extract_result_urls(data)
                if task_id in self._task_cache:
                    self._task_cache[task_id]["model_url"] = model_url
                    self._task_cache[task_id]["preview_url"] = preview_url
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.COMPLETED,
                    model_url=model_url,
                    preview_url=preview_url,
                )

            if status in {"failed", "error", "fail", "banned", "expired", "cancelled", "unknown"}:
                return GenerationResult(
                    task_id=task_id,
                    status=GenerationStatus.FAILED,
                    error_message=(
                        data.get("error")
                        or data.get("message")
                        or f"Task ended with status: {status}"
                    ),
                )

            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.PROCESSING,
            )
        except Exception as exc:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=str(exc),
            )

    async def get_model_url(self, task_id: str) -> Optional[str]:
        result = await self.get_status(task_id)
        return result.model_url

    def get_preview_url(self, task_id: str) -> Optional[str]:
        cache = self._task_cache.get(task_id)
        return cache.get("preview_url") if cache else None

    async def _upload_image(self, image_data: bytes, filename: str) -> Optional[str]:
        files = {
            "file": (filename, image_data, self._guess_mime_type(filename)),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        response = await self._client.post(
            f"{self.BASE_URL}/upload/sts",
            headers=headers,
            files=files,
        )

        if response.status_code != 200:
            return None

        body = response.json()
        if body.get("code") != 0:
            return None

        data = body.get("data", {})
        return data.get("image_token")

    def _handle_submit_response(self, response: httpx.Response, task_id: str) -> GenerationResult:
        if response.status_code not in [200, 201]:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=f"HTTP {response.status_code}: {response.text[:300]}",
            )

        body = response.json()
        if body.get("code") not in (0, None):
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=self._extract_error(body),
            )

        data = body.get("data", body)
        tripo_task_id = data.get("task_id")
        if not tripo_task_id:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=f"No task_id in response: {str(body)[:300]}",
            )

        self._task_cache[task_id] = {
            "tripo_task_id": tripo_task_id,
            "created_at": datetime.utcnow(),
        }
        return GenerationResult(task_id=task_id, status=GenerationStatus.PROCESSING)

    def _merge_generation_options(self, payload: Dict[str, Any], options: Dict[str, Any], text_mode: bool) -> None:
        model_version = options.get("model_version") or self.DEFAULT_MODEL_VERSION
        payload["model_version"] = model_version

        # Shared options documented for text_to_model/image_to_model
        passthrough_keys = [
            "face_limit",
            "texture",
            "pbr",
            "texture_quality",
            "auto_size",
            "quad",
            "smart_low_poly",
            "generate_parts",
            "export_uv",
            "geometry_quality",
            "model_seed",
            "texture_seed",
            "compress",
        ]

        for key in passthrough_keys:
            if key in options and options[key] is not None:
                payload[key] = options[key]

        if text_mode:
            if options.get("negative_prompt"):
                payload["negative_prompt"] = options["negative_prompt"]
            if options.get("image_seed") is not None:
                payload["image_seed"] = options["image_seed"]
        else:
            if options.get("enable_image_autofix") is not None:
                payload["enable_image_autofix"] = bool(options["enable_image_autofix"])
            if options.get("texture_alignment"):
                payload["texture_alignment"] = options["texture_alignment"]
            if options.get("orientation"):
                payload["orientation"] = options["orientation"]

    def _extract_result_urls(self, data: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        model_url = None
        preview_url = None

        # 0) Tripo polling doc: prefer output.*
        output = data.get("output") or {}
        if isinstance(output, dict):
            model_url = (
                output.get("model")
                or output.get("pbr_model")
                or output.get("base_model")
            )
            preview_url = (
                output.get("rendered_image")
                or output.get("generated_image")
            )

        # 1) File list style responses
        files = (
            data.get("ResultFile3Ds")
            or data.get("result_file_3ds")
            or data.get("resultFile3Ds")
            or data.get("files")
            or []
        )
        if isinstance(files, list):
            for entry in files:
                if not isinstance(entry, dict):
                    continue
                candidate = entry.get("Url") or entry.get("url")
                if candidate and self._looks_like_model_url(candidate):
                    model_url = model_url or candidate
                preview_url = preview_url or entry.get("PreviewImageUrl") or entry.get("preview_image_url")
            if not model_url and files and isinstance(files[0], dict):
                model_url = files[0].get("Url") or files[0].get("url")
                preview_url = preview_url or files[0].get("PreviewImageUrl") or files[0].get("preview_image_url")

        # 2) Direct/common keys
        if not model_url:
            model_url = (
                data.get("model_url")
                or data.get("modelUrl")
                or (data.get("model") or {}).get("url")
                or (data.get("output") or {}).get("model")
                or (data.get("output") or {}).get("model_url")
            )
        if not preview_url:
            preview_url = (
                data.get("preview_url")
                or data.get("thumbnail_url")
                or (data.get("output") or {}).get("rendered_image")
                or (data.get("output") or {}).get("thumbnail_url")
                or (data.get("output") or {}).get("preview_image_url")
            )

        # 3) Deep scan fallback for unknown response shapes
        if not model_url or not preview_url:
            scanned_model, scanned_preview = self._scan_urls(data)
            model_url = model_url or scanned_model
            preview_url = preview_url or scanned_preview

        return model_url, preview_url

    def _scan_urls(self, obj: Any) -> tuple[Optional[str], Optional[str]]:
        model_url = None
        preview_url = None

        def walk(node: Any):
            nonlocal model_url, preview_url
            if isinstance(node, dict):
                for _, value in node.items():
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
            elif isinstance(node, str) and node.startswith("http"):
                if not model_url and self._looks_like_model_url(node):
                    model_url = node
                elif not preview_url and self._looks_like_preview_url(node):
                    preview_url = node

        walk(obj)
        return model_url, preview_url

    def _looks_like_model_url(self, url: str) -> bool:
        u = url.lower()
        return any(ext in u for ext in [".glb", ".obj", ".fbx", ".usdz", ".stl", ".zip", ".mp4"])

    def _looks_like_preview_url(self, url: str) -> bool:
        u = url.lower()
        return any(ext in u for ext in [".png", ".jpg", ".jpeg", ".webp"])

    def _extract_error(self, body: Dict[str, Any]) -> str:
        message = body.get("message") or "Unknown error"
        suggestion = body.get("suggestion")
        code = body.get("code")
        if suggestion:
            return f"[{code}] {message}. Suggestion: {suggestion}"
        return f"[{code}] {message}"

    def _guess_file_type(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower().lstrip(".")
        if suffix in {"jpg", "jpeg", "png", "webp"}:
            return "jpg" if suffix == "jpeg" else suffix
        return "png"

    def _guess_mime_type(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if suffix == ".webp":
            return "image/webp"
        return "image/png"

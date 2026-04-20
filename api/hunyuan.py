import asyncio
import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple

import httpx

from .base import BaseAPI, GenerationResult, GenerationStatus


class HunyuanAPI(BaseAPI):
    provider_name = "hunyuan"
    supports_text = True
    supports_image = True
    supports_preview = True

    HOST = "ai3d.tencentcloudapi.com"
    BASE_URL = f"https://{HOST}"
    SERVICE = "ai3d"
    VERSION = "2025-05-13"
    DEFAULT_REGION = "ap-guangzhou"

    SUBMIT_ACTION_PRO = "SubmitHunyuanTo3DProJob"
    QUERY_ACTION_PRO = "QueryHunyuanTo3DProJob"
    SUBMIT_ACTION_RAPID = "SubmitHunyuanTo3DRapidJob"
    QUERY_ACTION_RAPID = "QueryHunyuanTo3DRapidJob"

    def __init__(self, api_key: str, secret_key: str = None, **kwargs):
        super().__init__(api_key, secret_key, **kwargs)
        self.secret_id, self.secret_key, self.token = self._resolve_credentials(api_key, secret_key)
        self.region = kwargs.get("region", self.DEFAULT_REGION)
        self._task_cache: Dict[str, Dict] = {}

    @staticmethod
    def _resolve_credentials(api_key: str, secret_key: Optional[str]) -> Tuple[str, Optional[str], Optional[str]]:
        # Backward compatible mode:
        # 1) Separate fields: api_key=SecretId, secret_key=SecretKey
        # 2) Single field: "SecretId|SecretKey" (also supports ":" "," or new line)
        # 3) STS temporary credentials:
        #    - Separate fields: api_key=SecretId, secret_key="SecretKey|Token"
        #    - Single field: "SecretId|SecretKey|Token"
        if secret_key:
            sid = (api_key or "").strip()
            raw_sk = (secret_key or "").strip()
            if "|" in raw_sk:
                sk, token = raw_sk.split("|", 1)
                sk = sk.strip()
                token = token.strip()
                return sid, (sk or None), (token or None)
            return sid, (raw_sk or None), None

        raw = (api_key or "").strip()
        if not raw:
            return "", None, None

        delimiters = ["|", "\n", ",", ":"]
        for delimiter in delimiters:
            if delimiter in raw:
                parts = [p.strip() for p in raw.split(delimiter) if p.strip()]
                if len(parts) >= 2:
                    sid = parts[0]
                    sk = parts[1]
                    token = parts[2] if len(parts) >= 3 else None
                    return sid, sk, token

        # Could be plain SecretId only (will fail with clear error later),
        # but keep it so users can see exactly what was provided.
        return raw, None, None

    async def generate_from_image(
        self,
        image_data: bytes,
        filename: str = "image.png",
        task_id: str = None,
        **kwargs,
    ) -> GenerationResult:
        task_id = task_id or str(uuid.uuid4())
        if not self.secret_id or not self.secret_key:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="Hunyuan API key format invalid. Please use 'SecretId|SecretKey'.",
            )
        if not self.secret_id.startswith("AKID"):
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="SecretId 格式异常：通常应以 AKID 开头，请检查 SecretId/SecretKey 是否填反。",
            )

        edition = str(kwargs.get("generation_edition", "pro")).lower()
        payload = self._build_submit_payload_from_image(image_data, kwargs, edition)
        action = self.SUBMIT_ACTION_RAPID if edition == "rapid" else self.SUBMIT_ACTION_PRO
        response = await self._post_tc3(action, payload)
        return self._handle_submit_response(response, task_id, edition)

    async def generate_from_text(
        self,
        text: str,
        task_id: str = None,
        **kwargs,
    ) -> GenerationResult:
        task_id = task_id or str(uuid.uuid4())
        if not self.secret_id or not self.secret_key:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="Hunyuan API key format invalid. Please use 'SecretId|SecretKey'.",
            )
        if not self.secret_id.startswith("AKID"):
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="SecretId 格式异常：通常应以 AKID 开头，请检查 SecretId/SecretKey 是否填反。",
            )

        edition = str(kwargs.get("generation_edition", "pro")).lower()
        payload = self._build_submit_payload_from_text(text, kwargs, edition)
        action = self.SUBMIT_ACTION_RAPID if edition == "rapid" else self.SUBMIT_ACTION_PRO
        response = await self._post_tc3(action, payload)
        return self._handle_submit_response(response, task_id, edition)

    async def get_status(self, task_id: str, job_id: str = None) -> GenerationResult:
        if not self.secret_id or not self.secret_key:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="Hunyuan API key format invalid. Please use 'SecretId|SecretKey'.",
            )

        if not job_id:
            cache = self._task_cache.get(task_id)
            if cache:
                job_id = cache.get("job_id")

        if not job_id:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message="JobId not found. Please provide job_id parameter.",
            )

        cache = self._task_cache.get(task_id, {})
        edition = str(cache.get("generation_edition", "")).lower()
        actions = []
        if edition == "rapid":
            actions = [self.QUERY_ACTION_RAPID]
        elif edition == "pro":
            actions = [self.QUERY_ACTION_PRO]
        else:
            actions = [self.QUERY_ACTION_PRO, self.QUERY_ACTION_RAPID]

        last_result = None
        for action in actions:
            response = await self._post_tc3(action, {"JobId": job_id})
            result, definitive = self._handle_query_response(response, task_id, job_id, action)
            last_result = result
            if definitive:
                return result

        return last_result or GenerationResult(
            task_id=task_id,
            status=GenerationStatus.FAILED,
            error_message="Failed to query Hunyuan job status.",
        )

    async def get_model_url(self, task_id: str) -> Optional[str]:
        result = await self.get_status(task_id)
        return result.model_url

    def get_preview_url(self, task_id: str) -> Optional[str]:
        cache = self._task_cache.get(task_id)
        return cache.get("preview_url") if cache else None

    async def poll_until_complete(
        self,
        task_id: str,
        job_id: str = None,
        interval: float = 10.0,
        max_wait: float = 600.0,
    ) -> GenerationResult:
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < max_wait:
            result = await self.get_status(task_id, job_id)
            if result.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED]:
                return result
            await asyncio.sleep(interval)
        return GenerationResult(
            task_id=task_id,
            status=GenerationStatus.FAILED,
            error_message="Generation timed out (max 10 minutes)",
        )

    def _build_submit_payload_from_image(self, image_data: bytes, options: Dict, edition: str) -> Dict:
        payload: Dict = {
            "ImageBase64": base64.b64encode(image_data).decode("utf-8"),
        }
        if edition == "rapid":
            self._merge_rapid_options(payload, options)
            return payload

        payload["Model"] = str(options.get("model", "3.0"))
        self._merge_pro_options(payload, options)
        prompt = (options.get("prompt") or "").strip()
        generate_type = str(options.get("generate_type", "Normal"))
        if prompt and generate_type == "Sketch":
            payload["Prompt"] = prompt
        return payload

    def _build_submit_payload_from_text(self, text: str, options: Dict, edition: str) -> Dict:
        payload: Dict = {"Prompt": text}
        if edition == "rapid":
            self._merge_rapid_options(payload, options)
            return payload

        payload["Model"] = str(options.get("model", "3.0"))
        self._merge_pro_options(payload, options)
        return payload

    def _merge_pro_options(self, payload: Dict, options: Dict) -> None:
        generate_type = str(options.get("generate_type", "Normal"))
        payload["GenerateType"] = generate_type

        if generate_type != "Geometry":
            payload["EnablePBR"] = bool(options.get("enable_pbr", False))

        if generate_type != "LowPoly":
            face_count = options.get("face_count")
            if isinstance(face_count, int):
                payload["FaceCount"] = max(3000, min(1500000, face_count))

        if generate_type == "LowPoly":
            polygon_type = options.get("polygon_type")
            if polygon_type in {"triangle", "quadrilateral"}:
                payload["PolygonType"] = polygon_type

        result_format = options.get("result_format")
        if result_format in {"STL", "USDZ", "FBX"}:
            payload["ResultFormat"] = result_format

    def _merge_rapid_options(self, payload: Dict, options: Dict) -> None:
        result_format = options.get("result_format")
        if result_format in {"OBJ", "GLB", "STL", "USDZ", "FBX", "MP4"}:
            payload["ResultFormat"] = result_format

        enable_pbr = options.get("enable_pbr")
        if enable_pbr is not None:
            payload["EnablePBR"] = bool(enable_pbr)

        enable_geometry = options.get("enable_geometry")
        if enable_geometry is not None:
            payload["EnableGeometry"] = bool(enable_geometry)
            # Geometry 模式不支持 OBJ，交给接口默认 GLB
            if payload["EnableGeometry"] and payload.get("ResultFormat") == "OBJ":
                payload.pop("ResultFormat", None)

    async def _post_tc3(self, action: str, payload: Dict) -> httpx.Response:
        # Keep content-type identical to Tencent TC3 examples.
        content_type = "application/json; charset=utf-8"
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        timestamp = int(time.time())

        headers = self._build_tc3_headers(
            action=action,
            payload_json=payload_json,
            timestamp=timestamp,
            content_type=content_type,
        )

        return await self._client.post(
            self.BASE_URL,
            headers=headers,
            content=payload_json.encode("utf-8"),
        )

    def _build_tc3_headers(
        self,
        action: str,
        payload_json: str,
        timestamp: int,
        content_type: str,
    ) -> Dict[str, str]:
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        action_lower = action.lower()
        signed_headers = "content-type;host;x-tc-action"

        canonical_headers = (
            f"content-type:{content_type}\n"
            f"host:{self.HOST}\n"
            f"x-tc-action:{action_lower}\n"
        )
        hashed_payload = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        canonical_request = "\n".join([
            "POST",
            "/",
            "",
            canonical_headers,
            signed_headers,
            hashed_payload,
        ])

        credential_scope = f"{date}/{self.SERVICE}/tc3_request"
        string_to_sign = "\n".join([
            "TC3-HMAC-SHA256",
            str(timestamp),
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])

        secret_date = hmac.new(("TC3" + self.secret_key).encode("utf-8"), date.encode("utf-8"), hashlib.sha256).digest()
        secret_service = hmac.new(secret_date, self.SERVICE.encode("utf-8"), hashlib.sha256).digest()
        secret_signing = hmac.new(secret_service, b"tc3_request", hashlib.sha256).digest()
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization = (
            "TC3-HMAC-SHA256 "
            f"Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": content_type,
            "Host": self.HOST,
            "X-TC-Action": action,
            "X-TC-Version": self.VERSION,
            "X-TC-Timestamp": str(timestamp),
        }
        if self.region:
            headers["X-TC-Region"] = self.region
        if self.token:
            headers["X-TC-Token"] = self.token
        return headers

    def _handle_submit_response(self, response: httpx.Response, task_id: str, edition: str) -> GenerationResult:
        response_json, parse_error = self._parse_json(response)
        if parse_error:
            return GenerationResult(task_id=task_id, status=GenerationStatus.FAILED, error_message=parse_error)

        if response.status_code != 200:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=self._extract_error_message(response_json) or f"HTTP {response.status_code}",
            )

        data = response_json.get("Response", {})
        error = data.get("Error", {})
        if error:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=self._extract_error_message(response_json)
                or f"[{error.get('Code', 'Unknown')}] {error.get('Message', 'Unknown error')}",
            )

        job_id = data.get("JobId")
        if not job_id:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=f"No JobId in response: {json.dumps(response_json, ensure_ascii=False)[:400]}",
            )

        self._task_cache[task_id] = {
            "job_id": job_id,
            "created_at": datetime.utcnow(),
            "generation_edition": edition,
        }
        return GenerationResult(task_id=task_id, status=GenerationStatus.PROCESSING, job_id=job_id)

    def _handle_query_response(
        self,
        response: httpx.Response,
        task_id: str,
        job_id: str,
        action: str,
    ) -> Tuple[GenerationResult, bool]:
        response_json, parse_error = self._parse_json(response)
        if parse_error:
            return GenerationResult(task_id=task_id, status=GenerationStatus.FAILED, error_message=parse_error), True

        if response.status_code != 200:
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=self._extract_error_message(response_json) or f"HTTP {response.status_code}",
            ), True

        data = response_json.get("Response", {})
        error = data.get("Error", {})
        if error:
            code = str(error.get("Code", ""))
            retryable = code in {"InvalidAction", "InvalidParameter", "InvalidParameterValue", "ResourceNotFound"}
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                error_message=self._extract_error_message(response_json)
                or f"[{error.get('Code', 'Unknown')}] {error.get('Message', 'Unknown error')}",
            ), (not retryable)

        status = str(data.get("Status", "")).upper()

        if status == "DONE":
            files = data.get("ResultFile3Ds") or []
            model_url = None
            preview_url = None
            for file_info in files:
                file_type = str(file_info.get("Type", "")).upper()
                if file_type == "GLB":
                    model_url = file_info.get("Url")
                    preview_url = file_info.get("PreviewImageUrl")
                    break
            if not model_url and files:
                model_url = files[0].get("Url")
                preview_url = files[0].get("PreviewImageUrl")

            if task_id in self._task_cache:
                self._task_cache[task_id]["preview_url"] = preview_url
                self._task_cache[task_id]["generation_edition"] = "rapid" if action == self.QUERY_ACTION_RAPID else "pro"

            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.COMPLETED,
                job_id=job_id,
                model_url=model_url,
                preview_url=preview_url,
            ), True

        if status == "FAIL":
            error_message = data.get("ErrorMessage") or data.get("ErrorCode") or "Generation failed"
            return GenerationResult(
                task_id=task_id,
                status=GenerationStatus.FAILED,
                job_id=job_id,
                error_message=str(error_message),
            ), True

        # WAIT / RUN 等视为处理中
        if status in {"WAIT", "RUN"}:
            if task_id in self._task_cache:
                self._task_cache[task_id]["generation_edition"] = "rapid" if action == self.QUERY_ACTION_RAPID else "pro"
            return GenerationResult(task_id=task_id, status=GenerationStatus.PROCESSING, job_id=job_id), True

        # 未识别状态可能是查错接口，尝试下一个 action
        return GenerationResult(
            task_id=task_id,
            status=GenerationStatus.FAILED,
            job_id=job_id,
            error_message=f"Unknown status: {status}",
        ), False

    def _parse_json(self, response: httpx.Response):
        try:
            return response.json(), None
        except Exception as exc:
            text = response.text[:400] if response.text else ""
            return None, f"Failed to parse response: {exc}. Raw: {text}"

    def _extract_error_message(self, response_json: Optional[Dict]) -> Optional[str]:
        if not isinstance(response_json, dict):
            return None
        data = response_json.get("Response", response_json)
        request_id = data.get("RequestId")

        error = data.get("Error")
        if isinstance(error, dict):
            code = str(error.get("Code", "Unknown"))
            message = str(error.get("Message", "Unknown error"))
            suffix = f" (RequestId: {request_id})" if request_id else ""
            if code == "AuthFailure.SignatureFailure":
                return (
                    f"[{code}] {message}{suffix}. "
                    "请检查 SecretId/SecretKey 是否同一对、是否已禁用、是否使用了临时凭证但未携带 Token。"
                )
            return f"[{code}] {message}{suffix}"

        for key in ["ErrorMessage", "Message", "message", "ErrorCode"]:
            if data.get(key):
                return str(data[key])
        return None

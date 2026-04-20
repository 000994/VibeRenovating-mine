from __future__ import annotations

import json
import os
import re
import base64
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

from config import ItemCategory, SecondaryTag, settings


@dataclass
class PromptRoutingResult:
    enhanced_prompt: str
    category: ItemCategory
    tags: List[SecondaryTag]
    source: str = "heuristic"
    raw_response: Optional[str] = None
    error_message: Optional[str] = None


DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_DASHSCOPE_ENDPOINT = f"{DEFAULT_DASHSCOPE_BASE_URL}/chat/completions"
DEFAULT_DASHSCOPE_MODEL = "qwen2.5-7b-instruct"
DEFAULT_DASHSCOPE_VISION_MODEL = "qwen2.5-vl-7b-instruct"
DEFAULT_ROUTER_ENDPOINT = (
    os.getenv("PROMPT_ROUTER_ENDPOINT")
    or settings.prompt_router_endpoint
    or DEFAULT_DASHSCOPE_ENDPOINT
)
DEFAULT_ROUTER_MODEL = (
    os.getenv("PROMPT_ROUTER_MODEL")
    or settings.prompt_router_model
    or DEFAULT_DASHSCOPE_MODEL
)
DEFAULT_ROUTER_VISION_MODEL = (
    os.getenv("PROMPT_ROUTER_VISION_MODEL")
    or settings.prompt_router_vision_model
    or DEFAULT_DASHSCOPE_VISION_MODEL
)

FRAME_SUPPORT_KEYWORDS = [
    "chair", "stool", "bar stool", "bed frame", "rack", "shelf", "hanger",
    "clothes hanger", "coat rack", "metal rack", "frame", "support", "stand",
    "椅子", "吧椅", "床架", "货架", "金属架", "衣架", "挂衣架", "支架", "框架",
]

SOFT_FLEXIBLE_KEYWORDS = [
    "sofa", "couch", "armchair", "loveseat", "recliner", "bean bag",
    "fabric", "leather", "upholstered", "cushion", "plush",
    "沙发", "软包", "布艺", "皮艺", "单人沙发", "双人沙发", "多人沙发", "懒人沙发", "靠垫",
]

ORGANIC_KEYWORDS = [
    "sculpture", "art toy", "decor figurine", "organic shape", "freeform",
    "异形", "雕塑", "装饰摆件", "植物造型", "仿生造型",
]


def enhance_and_route_text(
    user_prompt: str,
    use_llm: bool = True,
    model: str = DEFAULT_ROUTER_MODEL,
    endpoint: str = DEFAULT_ROUTER_ENDPOINT,
    timeout_sec: int = 20,
) -> PromptRoutingResult:
    prompt = (user_prompt or "").strip()
    if not prompt:
        return PromptRoutingResult(
            enhanced_prompt="",
            category=ItemCategory.ORGANIC,
            tags=[],
            source="heuristic",
            error_message="empty prompt",
        )

    if use_llm:
        llm_result = _try_llm_route(prompt, model=model, endpoint=endpoint, timeout_sec=timeout_sec)
        if llm_result is not None:
            return llm_result

    return _heuristic_route(prompt)


def enhance_and_route_image(
    image_data: bytes,
    filename: str = "image.png",
    use_llm: bool = True,
    model: str = DEFAULT_ROUTER_VISION_MODEL,
    endpoint: str = DEFAULT_ROUTER_ENDPOINT,
    timeout_sec: int = 30,
) -> PromptRoutingResult:
    if not image_data:
        return PromptRoutingResult(
            enhanced_prompt="",
            category=ItemCategory.ORGANIC,
            tags=[],
            source="heuristic",
            error_message="empty image",
        )

    if use_llm:
        llm_result = _try_llm_route_image(image_data, filename=filename, model=model, endpoint=endpoint, timeout_sec=timeout_sec)
        if llm_result is not None:
            return llm_result

    return PromptRoutingResult(
        enhanced_prompt="",
        category=ItemCategory.ORGANIC,
        tags=[],
        source="heuristic",
        error_message="image llm route failed",
    )


def _try_llm_route(
    user_prompt: str,
    model: str,
    endpoint: str,
    timeout_sec: int,
) -> Optional[PromptRoutingResult]:
    system = (
        "You are a prompt optimizer and product classifier for 3D model generation.\n"
        "Category policy:\n"
        "- frame_support includes: 椅子、床架、吧椅、货架、金属架、衣架 and similar frame/rack/support objects.\n"
        "- organic is for: 异形设计家具、雕塑、装饰摆件、植物造型件 and other freeform sculptural objects.\n"
        "Return JSON only with keys:\n"
        "enhanced_prompt: string,\n"
        "category: one of [box_panel, frame_support, soft_flexible, organic, scene],\n"
        "tags: array of zero or more from "
        "[transparent, high_reflective, multi_part, movable, hard_soft_mix, hollow, slender_support, complex_background].\n"
        "Do not include markdown."
    )
    payload_prompt = (
        f"{system}\n\n"
        f"User input:\n{user_prompt}\n\n"
        "Return compact JSON."
    )

    try:
        request_payload, request_headers = _build_request(endpoint, model, payload_prompt)
        if request_payload is None:
            return None

        with httpx.Client(timeout=timeout_sec, trust_env=False) as client:
            resp = client.post(endpoint, json=request_payload, headers=request_headers)
            resp.raise_for_status()
            data = resp.json()
            text = _extract_text_response(endpoint, data)
            parsed = _parse_llm_json(text)
            if not parsed:
                return None

            enhanced_prompt = str(parsed.get("enhanced_prompt") or user_prompt).strip()
            category_raw = str(parsed.get("category") or "").strip()
            tags_raw = parsed.get("tags") or []

            category = _to_category(category_raw)
            if category is None:
                return None

            category = _override_category_by_keywords(user_prompt, category)
            tags = _to_tags(tags_raw)
            return PromptRoutingResult(
                enhanced_prompt=enhanced_prompt or user_prompt,
                category=category,
                tags=tags,
                source="llm",
                raw_response=text,
            )
    except Exception:
        return None

    return None


def _try_llm_route_image(
    image_data: bytes,
    filename: str,
    model: str,
    endpoint: str,
    timeout_sec: int,
) -> Optional[PromptRoutingResult]:
    endpoint_lower = endpoint.lower()
    if not endpoint_lower.endswith("/chat/completions"):
        return None

    system = (
        "You are an image-to-3D prompt optimizer and product classifier.\n"
        "Category policy:\n"
        "- frame_support includes: 椅子、床架、吧椅、货架、金属架、衣架 and similar frame/rack/support objects.\n"
        "- organic is for: 异形设计家具、雕塑、装饰摆件、植物造型件 and other freeform sculptural objects.\n"
        "Return JSON only with keys:\n"
        "enhanced_prompt: string,\n"
        "category: one of [box_panel, frame_support, soft_flexible, organic, scene],\n"
        "tags: array of zero or more from "
        "[transparent, high_reflective, multi_part, movable, hard_soft_mix, hollow, slender_support, complex_background].\n"
        "Do not include markdown."
    )
    instruction = (
        "Analyze the uploaded image and output compact JSON according to the schema. "
        "enhanced_prompt should be a concise, production-ready text prompt for 3D generation."
    )

    api_key = _get_router_api_key()
    if not api_key:
        return None

    mime_type = _guess_image_mime_type(filename)
    image_b64 = base64.b64encode(image_data).decode("utf-8")
    data_url = f"data:{mime_type};base64,{image_b64}"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{system}\n\n{instruction}"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=timeout_sec, trust_env=False) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text = _extract_text_response(endpoint, data)
            parsed = _parse_llm_json(text)
            if not parsed:
                return None

            enhanced_prompt = str(parsed.get("enhanced_prompt") or "").strip()
            category_raw = str(parsed.get("category") or "").strip()
            tags_raw = parsed.get("tags") or []

            category = _to_category(category_raw)
            if category is None:
                return None

            category = _override_category_by_keywords(enhanced_prompt, category)
            tags = _to_tags(tags_raw)
            return PromptRoutingResult(
                enhanced_prompt=enhanced_prompt,
                category=category,
                tags=tags,
                source="llm",
                raw_response=text,
            )
    except Exception:
        return None

    return None


def _build_request(endpoint: str, model: str, payload_prompt: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, str]]]:
    endpoint_lower = endpoint.lower()

    if endpoint_lower.endswith("/chat/completions"):
        api_key = _get_router_api_key()
        if not api_key:
            return None, None

        return (
            {
                "model": model,
                "messages": [{"role": "user", "content": payload_prompt}],
                "temperature": 0.2,
            },
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    if endpoint_lower.endswith("/text-generation/generation") or endpoint_lower.endswith("/generation"):
        api_key = _get_router_api_key()
        if not api_key:
            return None, None

        return (
            {
                "model": model,
                "input": {"prompt": payload_prompt},
                "parameters": {"temperature": 0.2},
            },
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    raise ValueError(
        "Unsupported LLM endpoint. Use DashScope compatible-mode "
        "(/chat/completions) or text-generation (/generation) API."
    )


def _extract_text_response(endpoint: str, data: Dict[str, Any]) -> str:
    endpoint_lower = endpoint.lower()

    if endpoint_lower.endswith("/chat/completions"):
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        return str(message.get("content", "")).strip()

    if endpoint_lower.endswith("/text-generation/generation") or endpoint_lower.endswith("/generation"):
        output = data.get("output") or {}
        return str(output.get("text", "")).strip()

    raise ValueError("Unsupported LLM response format for current endpoint.")


def _parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _to_category(value: str) -> Optional[ItemCategory]:
    normalized = value.strip().lower()
    for category in ItemCategory:
        if category.value == normalized:
            return category
    return None


def _to_tags(values: Any) -> List[SecondaryTag]:
    result: List[SecondaryTag] = []
    if not isinstance(values, list):
        return result
    for item in values:
        normalized = str(item).strip().lower()
        for tag in SecondaryTag:
            if tag.value == normalized and tag not in result:
                result.append(tag)
    return result


def _heuristic_route(user_prompt: str) -> PromptRoutingResult:
    p = user_prompt.lower()
    tags: List[SecondaryTag] = []

    if any(k in p for k in ["glass", "transparent", "acrylic", "透", "透明"]):
        tags.append(SecondaryTag.TRANSPARENT)
    if any(k in p for k in ["metal", "chrome", "reflect", "mirror", "金属", "反光"]):
        tags.append(SecondaryTag.HIGH_REFLECTIVE)
    if any(k in p for k in ["module", "component", "part", "组合", "多部件"]):
        tags.append(SecondaryTag.MULTI_PART)
    if any(k in p for k in ["movable", "door", "drawer", "hinge", "可动", "开合"]):
        tags.append(SecondaryTag.MOVABLE)
    if any(k in p for k in ["soft", "fabric", "leather", "sofa", "cushion", "软包", "布艺"]):
        tags.append(SecondaryTag.HARD_SOFT_MIX)
    if any(k in p for k in ["hollow", "openwork", "镂空", "空心"]):
        tags.append(SecondaryTag.HOLLOW)
    if any(k in p for k in ["slender", "thin leg", "support", "细长", "支撑"]):
        tags.append(SecondaryTag.SLENDER_SUPPORT)
    if any(k in p for k in ["scene", "room", "interior", "场景", "室内", "客厅", "卧室"]):
        tags.append(SecondaryTag.COMPLEX_BACKGROUND)

    if any(k in p for k in ["scene", "room", "interior", "场景", "室内", "客厅", "卧室"]):
        category = ItemCategory.SCENE
    elif any(k in p for k in ["sofa", "fabric", "leather", "cushion", "软包", "布艺"]):
        category = ItemCategory.SOFT_FLEXIBLE
    elif any(k in p for k in FRAME_SUPPORT_KEYWORDS):
        category = ItemCategory.FRAME_SUPPORT
    elif any(k in p for k in ["cabinet", "box", "panel", "柜", "盒", "板"]):
        category = ItemCategory.BOX_PANEL
    else:
        category = ItemCategory.ORGANIC

    category = _override_category_by_keywords(user_prompt, category)

    enhanced = (
        f"{user_prompt.strip()}。"
        "请生成高质量3D模型，保持结构完整、比例准确、材质合理，"
        "输出可直接使用的网格与纹理。"
    )
    return PromptRoutingResult(
        enhanced_prompt=enhanced,
        category=category,
        tags=tags,
        source="heuristic",
    )


def _override_category_by_keywords(user_prompt: str, current: ItemCategory) -> ItemCategory:
    p = user_prompt.lower()
    # Priority: scene > soft_flexible > frame_support > organic
    if any(k in p for k in ["scene", "room", "interior", "场景", "室内", "客厅", "卧室"]):
        return ItemCategory.SCENE
    if any(k in p for k in SOFT_FLEXIBLE_KEYWORDS):
        return ItemCategory.SOFT_FLEXIBLE
    if any(k in p for k in FRAME_SUPPORT_KEYWORDS):
        return ItemCategory.FRAME_SUPPORT
    if any(k in p for k in ORGANIC_KEYWORDS):
        return ItemCategory.ORGANIC
    return current


def _guess_image_mime_type(filename: str) -> str:
    suffix = os.path.splitext((filename or "").lower())[1]
    if suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"


def _get_router_api_key() -> Optional[str]:
    return (
        os.getenv("PROMPT_ROUTER_API_KEY")
        or settings.prompt_router_api_key
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

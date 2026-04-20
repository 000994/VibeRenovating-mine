from typing import List, Tuple, Optional
from config import ItemCategory, SecondaryTag, GenerateMode, APIProvider


TAG_PREFERENCES = {
    SecondaryTag.HIGH_REFLECTIVE: [APIProvider.HUNYUAN, APIProvider.RODIN, APIProvider.TRIPO],
    SecondaryTag.HOLLOW: [APIProvider.RODIN],
    SecondaryTag.SLENDER_SUPPORT: [APIProvider.RODIN],
    SecondaryTag.COMPLEX_BACKGROUND: [APIProvider.HUNYUAN],
    SecondaryTag.HARD_SOFT_MIX: [APIProvider.MESHY],
    SecondaryTag.TRANSPARENT: [],
    SecondaryTag.MULTI_PART: [],
    SecondaryTag.MOVABLE: [],
}


CATEGORY_PREVIEW_API = {
    ItemCategory.BOX_PANEL: APIProvider.SF3D,
    ItemCategory.FRAME_SUPPORT: APIProvider.TRIPO,
    ItemCategory.SOFT_FLEXIBLE: APIProvider.SF3D,
    ItemCategory.ORGANIC: APIProvider.SF3D,
    ItemCategory.SCENE: APIProvider.HUNYUAN,
}


CATEGORY_FINE_API = {
    ItemCategory.BOX_PANEL: [APIProvider.SF3D, APIProvider.TRIPO, APIProvider.MESHY],
    ItemCategory.FRAME_SUPPORT: [APIProvider.RODIN],
    ItemCategory.SOFT_FLEXIBLE: [APIProvider.MESHY],
    ItemCategory.ORGANIC: [APIProvider.SF3D, APIProvider.TRIPO, APIProvider.MESHY],
    ItemCategory.SCENE: [APIProvider.HUNYUAN],
}


def route_api(
    category: ItemCategory,
    secondary_tags: List[SecondaryTag],
    mode: GenerateMode,
    available_providers: List[APIProvider] = None,
) -> APIProvider:
    if mode == GenerateMode.PREVIEW:
        base_provider = CATEGORY_PREVIEW_API.get(category, APIProvider.SF3D)
        if available_providers and base_provider not in available_providers:
            return get_first_available(CATEGORY_FINE_API.get(category, [APIProvider.SF3D]), available_providers)
        return base_provider
    
    candidates = CATEGORY_FINE_API.get(category, [APIProvider.SF3D])
    
    for tag in secondary_tags:
        tag_prefs = TAG_PREFERENCES.get(tag, [])
        for pref in tag_prefs:
            if pref in candidates:
                if available_providers and pref in available_providers:
                    return pref
                elif not available_providers:
                    return pref
    
    if available_providers:
        return get_first_available(candidates, available_providers)
    
    return candidates[0] if candidates else APIProvider.SF3D


def get_first_available(candidates: List[APIProvider], available: List[APIProvider]) -> APIProvider:
    for provider in candidates:
        if provider in available:
            return provider
    return available[0] if available else candidates[0]


def get_recommended_apis(
    category: ItemCategory,
    secondary_tags: List[SecondaryTag],
) -> dict:
    preview_api = CATEGORY_PREVIEW_API.get(category, APIProvider.SF3D)
    fine_candidates = CATEGORY_FINE_API.get(category, [APIProvider.SF3D])
    
    tag_recommended = []
    for tag in secondary_tags:
        tag_prefs = TAG_PREFERENCES.get(tag, [])
        for pref in tag_prefs:
            if pref in fine_candidates:
                tag_recommended.append((tag, pref))
    
    return {
        "preview": preview_api,
        "fine_candidates": fine_candidates,
        "tag_recommended": tag_recommended,
    }


def get_api_description(provider: APIProvider) -> str:
    descriptions = {
        APIProvider.SF3D: "Stable Fast 3D - 极速生成(0.5秒)，适合箱体/平板类快速预览",
        APIProvider.MESHY: "Meshy - 支持文本和图片，软包类最佳，支持硬软混合",
        APIProvider.RODIN: "Rodin - 框架类最佳，镂空/细长支撑最出色",
        APIProvider.HUNYUAN: "混元3D - 腾讯出品，场景类最佳，高反光/背景复杂表现好",
        APIProvider.TRIPO: "Tripo - 快速生成，框架类预览推荐",
    }
    return descriptions.get(provider, provider.value)

from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum
from pathlib import Path

class ItemCategory(str, Enum):
    BOX_PANEL = "box_panel"
    FRAME_SUPPORT = "frame_support"
    SOFT_FLEXIBLE = "soft_flexible"
    ORGANIC = "organic"
    SCENE = "scene"

class SecondaryTag(str, Enum):
    TRANSPARENT = "transparent"
    HIGH_REFLECTIVE = "high_reflective"
    MULTI_PART = "multi_part"
    MOVABLE = "movable"
    HARD_SOFT_MIX = "hard_soft_mix"
    HOLLOW = "hollow"
    SLENDER_SUPPORT = "slender_support"
    COMPLEX_BACKGROUND = "complex_background"

class GenerateMode(str, Enum):
    PREVIEW = "preview"
    FINE = "fine"

class APIProvider(str, Enum):
    SF3D = "sf3d"
    MESHY = "meshy"
    RODIN = "rodin"
    HUNYUAN = "hunyuan"
    TRIPO = "tripo"

CATEGORY_NAMES = {
    ItemCategory.BOX_PANEL: "箱体/平板类",
    ItemCategory.FRAME_SUPPORT: "框架/支撑类",
    ItemCategory.SOFT_FLEXIBLE: "软包/柔性类",
    ItemCategory.ORGANIC: "自由曲面/有机类",
    ItemCategory.SCENE: "场景类",
}

TAG_NAMES = {
    SecondaryTag.TRANSPARENT: "透明",
    SecondaryTag.HIGH_REFLECTIVE: "高反光",
    SecondaryTag.MULTI_PART: "多部件",
    SecondaryTag.MOVABLE: "可动",
    SecondaryTag.HARD_SOFT_MIX: "硬软混合",
    SecondaryTag.HOLLOW: "镂空多",
    SecondaryTag.SLENDER_SUPPORT: "细长支撑",
    SecondaryTag.COMPLEX_BACKGROUND: "背景复杂",
}

CATEGORY_EXAMPLES = {
    ItemCategory.BOX_PANEL: "柜子、桌子、电视柜、床头柜",
    ItemCategory.FRAME_SUPPORT: "椅子、床架、吧椅、货架、金属架、衣架",
    ItemCategory.SOFT_FLEXIBLE: "沙发、软床、靠垫椅、布艺凳",
    ItemCategory.ORGANIC: "异形设计家具、雕塑、装饰摆件、植物造型件",
    ItemCategory.SCENE: "室内场景、室外场景、组合场景",
}

class Settings(BaseSettings):
    _project_root = Path(__file__).resolve().parent
    database_url: str = f"sqlite:///{(_project_root / 'viberenovating.db').as_posix()}"
    output_dir: str = "./output"
    max_file_size: int = 10 * 1024 * 1024
    
    sf3d_api_key: Optional[str] = None
    meshy_api_key: Optional[str] = None
    rodin_api_key: Optional[str] = None
    hunyuan_api_key: Optional[str] = None
    hunyuan_secret_key: Optional[str] = None
    tripo_api_key: Optional[str] = None
    prompt_router_api_key: Optional[str] = None
    prompt_router_model: Optional[str] = None
    prompt_router_vision_model: Optional[str] = None
    prompt_router_endpoint: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

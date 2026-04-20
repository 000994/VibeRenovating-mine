import streamlit as st
import asyncio
import base64
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from config import (
    ItemCategory, SecondaryTag, GenerateMode, APIProvider,
    CATEGORY_NAMES, TAG_NAMES, CATEGORY_EXAMPLES,
)
from core.classifier import get_all_categories, get_all_tags, get_category_description
from core.router import route_api, get_recommended_apis, get_api_description
from core.prompt_router import enhance_and_route_text, enhance_and_route_image
from core.generator import Generator, GenerationTask
from core.background_runner import (
    start_generation_task,
    get_generation_task_state,
    list_running_task_ids,
)
from models.database import Database
from utils.storage import StorageManager
from api import GenerationStatus
from assets.style import inject_custom_css

db = Database()
generator = Generator(db=db)
storage = StorageManager()

st.set_page_config(
    page_title="3D生成",
    page_icon="🎲",
    layout="wide",
)

inject_custom_css()

# ===================== 页面级自定义样式 =====================
st.markdown(
    """
    <style>
    .gen-hero {
        background: linear-gradient(135deg, #f5f0e8 0%, #ede6db 100%);
        border-radius: 20px;
        padding: 22px 28px;
        color: #2d2a26;
        margin-bottom: 20px;
        box-shadow: 0 4px 16px rgba(45, 42, 38, 0.06);
        border: 1px solid #e8e4df;
    }
    .gen-hero h1 {
        -webkit-text-fill-color: #2d2a26 !important;
        color: #2d2a26 !important;
        font-size: 1.6rem !important;
        margin-bottom: 4px !important;
        font-weight: 700 !important;
    }
    .gen-hero p {
        font-size: 0.95rem;
        color: #6b6560;
        margin: 0;
    }
    .task-card-custom {
        background: white;
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        border: 1px solid #e8e4df;
    }
    .task-header-custom {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .task-id-label {
        font-family: monospace;
        font-size: 0.85rem;
        color: #6b6560;
        background: #f0eeeb;
        padding: 4px 10px;
        border-radius: 8px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .status-running { background: #f5e6d8; color: #8a5a3a; }
    .status-success { background: #e3efe3; color: #4a6b4a; }
    .status-error   { background: #f5e0e0; color: #8a4a4a; }
    .status-pending { background: #f0eeeb; color: #5a5550; }
    /* 隐藏默认radio，配合自定义卡片使用 */
    .mode-radio .stRadio > div[role="radiogroup"] {
        flex-direction: row;
        gap: 10px;
    }
    .mode-radio .stRadio > div[role="radiogroup"] > label {
        flex: 1;
        min-width: 0;
    }
    .mode-radio .stRadio > div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_user_api_keys() -> Dict[APIProvider, Dict]:
    keys = db.get_all_api_keys()
    result = {}
    for provider_str, key_info in keys.items():
        try:
            provider = APIProvider(provider_str)
            result[provider] = key_info
        except ValueError:
            continue
    return result


def check_api_keys() -> List[APIProvider]:
    keys = get_user_api_keys()
    return list(keys.keys())


def show_3d_model(model_path: str):
    path = Path(model_path)
    if not path.exists():
        st.warning(f"模型文件不存在: {model_path}")
        return

    with open(path, "rb") as f:
        model_data = f.read()

    model_base64 = base64.b64encode(model_data).decode()

    html_code = f"""
    <div style="width: 100%; height: 500px; position: relative; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
        <model-viewer 
            id="model-viewer"
            src="data:model/gltf-binary;base64,{model_base64}"
            alt="3D Model"
            auto-camera-controls
            camera-controls
            touch-action="pan-y"
            style="width: 100%; height: 100%; background-color: #f7f5f2;"
            shadow-intensity="1"
            environment-image="neutral"
            rotation-per-second="0deg"
        ></model-viewer>
    </div>
    <script type="module">
        import 'https://ajax.googleapis.com/ajax/libs/model-viewer/3.0.1/model-viewer.min.js';
    </script>
    """
    st.components.v1.html(html_code, height=520)


def _init_generation_state():
    if "active_generation_task_ids" not in st.session_state:
        st.session_state.active_generation_task_ids = []


def _add_active_task(task_id: str):
    task_ids = st.session_state.active_generation_task_ids
    if task_id in task_ids:
        task_ids.remove(task_id)
    task_ids.insert(0, task_id)
    st.session_state.active_generation_task_ids = task_ids[:20]


# ===================== 页面顶部 =====================
st.markdown(
    """
    <div class="gen-hero">
        <h1>🎲 3D模型生成</h1>
        <p>上传图片或输入描述，AI 自动匹配分类、标签与最佳生成引擎</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===================== 步骤条 =====================
st.markdown(
    """
    <div class="step-bar">
        <div class="step-bar-item active">
            <div class="step-bar-num">1</div>
            <span>输入内容</span>
        </div>
        <div class="step-bar-arrow">›</div>
        <div class="step-bar-item active">
            <div class="step-bar-num">2</div>
            <span>智能配置</span>
        </div>
        <div class="step-bar-arrow">›</div>
        <div class="step-bar-item">
            <div class="step-bar-num">3</div>
            <span>提交生成</span>
        </div>
        <div class="step-bar-arrow">›</div>
        <div class="step-bar-item">
            <div class="step-bar-num">4</div>
            <span>查看结果</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===================== Step 1: 输入内容 =====================
with st.container():
    st.markdown("<div class='lite-card-title'>📤 输入内容</div>", unsafe_allow_html=True)

    input_type = st.radio(
        "选择输入类型",
        ["上传图片", "输入文本"],
        label_visibility="collapsed",
        horizontal=True,
    )

    image_data = None
    text_input = None
    uploaded_file = None

    if input_type == "上传图片":
        uploaded_file = st.file_uploader(
            "上传图片",
            type=["png", "jpg", "jpeg", "webp"],
            help="支持 PNG、JPG、JPEG、WEBP 格式",
            label_visibility="collapsed",
        )
        if uploaded_file:
            image_data = uploaded_file.read()
            preview_cols = st.columns([1, 3])
            with preview_cols[0]:
                st.image(image_data, caption="上传预览", use_container_width=True)
            with preview_cols[1]:
                st.markdown(
                    f"""
                    <div style="padding:14px 16px; background:#f7f5f2; border-radius:12px; border:1px solid #e8e4df;">
                        <div style="font-size:0.85rem; color:#6b6560; margin-bottom:4px;">文件名</div>
                        <div style="font-weight:500; color:#2d2a26; margin-bottom:10px;">{uploaded_file.name}</div>
                        <div style="font-size:0.85rem; color:#6b6560; margin-bottom:4px;">大小</div>
                        <div style="font-weight:500; color:#2d2a26;">{len(image_data) / 1024:.1f} KB</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        text_input = st.text_area(
            "物品描述",
            placeholder="例如：一个现代风格的木质办公桌，带有抽屉和金属桌腿...",
            height=100,
            label_visibility="collapsed",
        )

    # AI 图片路由结果
    image_route_result = None
    image_route_applied = False
    new_image_routed = False
    if image_data:
        image_hash = hashlib.md5(image_data).hexdigest()
        cached_hash = st.session_state.get("image_route_hash")
        cached_result = st.session_state.get("image_route_result")
        if cached_hash == image_hash and cached_result:
            image_route_result = cached_result
        else:
            image_route_result = enhance_and_route_image(
                image_data=image_data,
                filename=uploaded_file.name if uploaded_file else "image.png",
                use_llm=True,
            )
            st.session_state["image_route_hash"] = image_hash
            st.session_state["image_route_result"] = image_route_result
            new_image_routed = True

        image_route_applied = bool(image_route_result and image_route_result.source == "llm")
        if image_route_applied:
            tag_display = ", ".join([TAG_NAMES[t] for t in image_route_result.tags]) if image_route_result.tags else "无"
            st.success(
                f"🧠 AI 已自动识别：{CATEGORY_NAMES[image_route_result.category]} 丨 标签：{tag_display}"
            )
        else:
            st.warning("⚠️ 图片自动识别失败，请在下方案手动选择分类和标签")

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# ===================== Step 2: 智能配置区 =====================
with st.container():
    st.markdown("<div class='lite-card-title'>⚙️ 智能配置</div>", unsafe_allow_html=True)

    cfg_left, cfg_right = st.columns([1.2, 1])

    # --- 左侧：分类 + 标签 ---
    with cfg_left:
        st.markdown("<div style='font-weight:600; color:#2d2a26; margin-bottom:8px; font-size:0.95rem;'>📂 物品分类与标签</div>", unsafe_allow_html=True)

        categories = get_all_categories()
        category_options = {name: cat for cat, name in categories}
        category_name_by_enum = {cat: name for cat, name in categories}
        category_names = list(category_options.keys())

        if "auto_category_select" not in st.session_state:
            st.session_state["auto_category_select"] = category_names[0] if category_names else None
        if "auto_tag_select" not in st.session_state:
            st.session_state["auto_tag_select"] = []

        if image_route_applied and image_route_result is not None and new_image_routed:
            auto_category_name = category_name_by_enum.get(image_route_result.category)
            if auto_category_name in category_names:
                st.session_state["auto_category_select"] = auto_category_name

            tags = get_all_tags()
            tag_name_by_enum_tmp = {tag: name for tag, name in tags}
            auto_tag_names = [tag_name_by_enum_tmp[t] for t in image_route_result.tags if t in tag_name_by_enum_tmp]
            st.session_state["auto_tag_select"] = auto_tag_names

        cat_col, tag_col = st.columns([1, 1])
        with cat_col:
            selected_category_name = st.selectbox(
                "Main Category",
                category_names,
                key="auto_category_select",
                help="上传图片后会自动识别，你也可以手动调整",
                label_visibility="collapsed",
            )
            selected_category = category_options[selected_category_name]
            st.markdown(
                f"<div style='font-size:0.8rem; color:#9a9590; margin-top:4px;'>💡 {CATEGORY_EXAMPLES.get(selected_category, '')}</div>",
                unsafe_allow_html=True,
            )

        with tag_col:
            tags = get_all_tags()
            tag_options = {name: tag for tag, name in tags}
            selected_tag_names = st.multiselect(
                "Secondary Tags",
                list(tag_options.keys()),
                key="auto_tag_select",
                help="上传图片后会自动识别，你也可以手动调整",
                label_visibility="collapsed",
                placeholder="选择二级标签",
            )
            selected_tags = [tag_options[name] for name in selected_tag_names]

    # --- 右侧：生成模式 + API ---
    with cfg_right:
        st.markdown("<div style='font-weight:600; color:#2d2a26; margin-bottom:8px; font-size:0.95rem;'>🚀 生成模式与引擎</div>", unsafe_allow_html=True)

        mode_options = {"快速预览": GenerateMode.PREVIEW, "精细生成": GenerateMode.FINE}
        mode_icons = {"快速预览": "⚡", "精细生成": "💎"}
        mode_desc = {"快速预览": "快速验证结构", "精细生成": "高质量最终模型"}

        available_providers = check_api_keys()
        effective_available_providers = available_providers
        if input_type == "输入文本":
            effective_available_providers = [p for p in available_providers if p != APIProvider.SF3D]

        recommended = get_recommended_apis(selected_category, selected_tags)
        recommended_provider = route_api(
            selected_category,
            selected_tags,
            list(mode_options.values())[0],  # 默认先按快速预览推荐，后面再按实际选的模式更新
            effective_available_providers,
        )

        # 模式选择 + API 推荐 上下排列
        mode_col1, mode_col2 = st.columns(2)
        current_mode = st.session_state.get("gen_mode_name", "快速预览")
        with mode_col1:
            m_name = "快速预览"
            is_active = current_mode == m_name
            label = f"{'✅ ' if is_active else ''}{mode_icons[m_name]} {m_name}\n\n{mode_desc[m_name]}"
            if st.button(
                label,
                key=f"mode_btn_{m_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["gen_mode_name"] = m_name
                st.rerun()
        with mode_col2:
            m_name = "精细生成"
            is_active = current_mode == m_name
            label = f"{'✅ ' if is_active else ''}{mode_icons[m_name]} {m_name}\n\n{mode_desc[m_name]}"
            if st.button(
                label,
                key=f"mode_btn_{m_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["gen_mode_name"] = m_name
                st.rerun()

        selected_mode_name = st.session_state.get("gen_mode_name", "快速预览")
        selected_mode = mode_options[selected_mode_name]

        # 重新计算推荐（根据实际选中的模式）
        recommended_provider = route_api(
            selected_category,
            selected_tags,
            selected_mode,
            effective_available_providers,
        )

        if effective_available_providers:
            api_desc = get_api_description(recommended_provider)
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #f0f5f0 0%, #e3efe3 100%); border-radius: 10px; padding: 10px 12px; border: 1px solid #c8d8c8; margin-top: 10px;">
                    <div style="font-weight:600; color:#4a6b4a; font-size:0.9rem;">✨ 推荐引擎：{recommended_provider.value}</div>
                    <div style="font-size:0.8rem; color:#5a7a5a; margin-top:2px;">{api_desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 标签推荐 chips
            if recommended["tag_recommended"]:
                chips_html = ""
                for tag, provider in recommended["tag_recommended"]:
                    if provider in effective_available_providers:
                        chips_html += f'<span class="recommend-chip">{TAG_NAMES[tag]} → {provider.value}</span>'
                if chips_html:
                    st.markdown(f"<div style='margin-top:8px;'>{chips_html}</div>", unsafe_allow_html=True)
        else:
            if input_type == "输入文本" and APIProvider.SF3D in available_providers:
                st.warning("文本生成不支持 SF3D。请配置其他可用 API（如 Tripo / Meshy / 混元）。", icon="⚠️")
            else:
                st.warning("请先在设置页面配置 API 密钥", icon="⚠️")

        provider_options = {"自动选择（推荐）": None}
        for provider in APIProvider:
            if provider in effective_available_providers:
                provider_options[get_api_description(provider)] = provider

        selected_provider_name = st.selectbox(
            "选择API提供商",
            list(provider_options.keys()),
            help="选择自动会根据分类和标签智能推荐",
            label_visibility="collapsed",
        )
        selected_provider = provider_options[selected_provider_name]

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# ===================== Step 3: 高级参数（默认折叠） =====================
active_provider = selected_provider or recommended_provider

sf3d_generation_options: Dict[str, Any] = {}
hunyuan_generation_options: Dict[str, Any] = {}
tripo_generation_options: Dict[str, Any] = {}

with st.expander("🔧 高级参数", expanded=False):
    if active_provider == APIProvider.SF3D:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sf3d_texture_resolution = st.selectbox(
                "Texture Resolution",
                [512, 1024, 2048],
                index=1,
                help="Texture map resolution. 1024 is usually a good default.",
            )
        with c2:
            sf3d_foreground_ratio = st.slider(
                "Foreground Ratio",
                min_value=0.10,
                max_value=1.00,
                value=0.85,
                step=0.01,
                help="Lower values add more padding around the object.",
            )
        with c3:
            sf3d_remesh = st.selectbox(
                "Remesh",
                ["none", "triangle", "quad"],
                index=0,
            )
        with c4:
            sf3d_vertex_count = st.number_input(
                "Vertex Count (-1 = no limit)",
                min_value=-1,
                max_value=20000,
                value=-1,
                step=100,
            )
        sf3d_generation_options = {
            "texture_resolution": int(sf3d_texture_resolution),
            "foreground_ratio": float(sf3d_foreground_ratio),
            "remesh": sf3d_remesh,
            "vertex_count": int(sf3d_vertex_count),
        }
    elif active_provider == APIProvider.HUNYUAN:
        edition = st.selectbox("版本", ["专业版(Pro)", "极速版(Rapid)"], index=0)
        if edition == "极速版(Rapid)":
            col_a, col_b = st.columns(2)
            with col_a:
                enable_geometry = st.checkbox("开启单几何白模", value=False)
            with col_b:
                enable_pbr = st.checkbox("开启 PBR 材质", value=False)
            rapid_formats = ["默认(OBJ)", "OBJ", "GLB", "STL", "USDZ", "FBX", "MP4"]
            if enable_geometry:
                rapid_formats = ["默认(GLB)", "GLB", "STL", "USDZ", "FBX", "MP4"]
            rapid_format = st.selectbox("输出格式", rapid_formats, index=0)
            rapid_map = {
                "默认(OBJ)": None,
                "默认(GLB)": None,
                "OBJ": "OBJ",
                "GLB": "GLB",
                "STL": "STL",
                "USDZ": "USDZ",
                "FBX": "FBX",
                "MP4": "MP4",
            }
            hunyuan_generation_options = {
                "generation_edition": "rapid",
                "enable_pbr": enable_pbr,
                "enable_geometry": enable_geometry,
                "result_format": rapid_map[rapid_format],
            }
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                model_ver = st.selectbox("模型版本", ["3.0", "3.1"], index=0)
            with col_b:
                generate_type = st.selectbox("生成类型", ["Normal", "LowPoly", "Geometry", "Sketch"], index=0)
            enable_pbr = st.checkbox("开启 PBR 材质", value=False, disabled=(generate_type == "Geometry"))
            face_count = None
            polygon_type = None
            if generate_type != "LowPoly":
                face_count = st.slider("面数 FaceCount", min_value=3000, max_value=1500000, value=500000, step=1000)
            else:
                polygon_type = st.selectbox("多边形类型", ["triangle", "quadrilateral"], index=0)
            result_format = st.selectbox("输出格式", ["默认(GLB/OBJ)", "STL", "USDZ", "FBX"], index=0)
            format_map = {
                "默认(GLB/OBJ)": None,
                "STL": "STL",
                "USDZ": "USDZ",
                "FBX": "FBX",
            }
            hunyuan_generation_options = {
                "generation_edition": "pro",
                "model": model_ver,
                "generate_type": generate_type,
                "enable_pbr": enable_pbr,
                "face_count": face_count,
                "polygon_type": polygon_type,
                "result_format": format_map[result_format],
            }
    elif active_provider == APIProvider.TRIPO:
        c1, c2, c3 = st.columns(3)
        with c1:
            tripo_model_version = st.selectbox(
                "Model Version",
                [
                    "P1-20260311",
                    "Turbo-v1.0-20250506",
                    "v3.1-20260211",
                    "v3.0-20250812",
                    "v2.5-20250123",
                    "v2.0-20240919",
                    "v1.4-20240625",
                ],
                index=4,
                help="默认使用 v2.5-20250123。",
            )
        with c2:
            tripo_face_limit = st.number_input(
                "Face Limit (0=自动)",
                min_value=0,
                max_value=20000,
                value=0,
                step=500,
            )
        with c3:
            tripo_texture_quality = st.selectbox(
                "Texture Quality",
                ["", "standard", "detailed"],
                index=0,
            )

        tripo_negative_prompt = st.text_input(
            "Negative Prompt (文本生成可选)",
            value="",
            help="仅 text_to_model 时生效。",
        )

        chk1, chk2, chk3, chk4, chk5, chk6, chk7 = st.columns(7)
        with chk1:
            tripo_texture = st.checkbox("Enable Texture", value=True)
        with chk2:
            tripo_pbr = st.checkbox("Enable PBR", value=False)
        with chk3:
            tripo_quad = st.checkbox("Enable Quad Mesh", value=False)
        with chk4:
            tripo_smart_low_poly = st.checkbox("Smart Low Poly", value=False)
        with chk5:
            tripo_auto_size = st.checkbox("Auto Size", value=False)
        with chk6:
            tripo_enable_image_autofix = st.checkbox("Image AutoFix", value=True)
        with chk7:
            tripo_generate_parts = st.checkbox("Generate Parts", value=False)

        tripo_export_uv = st.checkbox("Export UV", value=True)

        c4, c5, c6 = st.columns(3)
        with c4:
            tripo_geometry_quality = st.selectbox(
                "Geometry Quality",
                ["", "standard", "detailed"],
                index=0,
            )
        with c5:
            tripo_texture_alignment = st.selectbox(
                "Texture Alignment (图生3D)",
                ["", "original_image", "geometry"],
                index=0,
            )
        with c6:
            tripo_orientation = st.selectbox(
                "Orientation (图生3D)",
                ["", "default", "align_image"],
                index=0,
            )

        tripo_compress = st.selectbox(
            "Compression",
            ["", "meshopt", "geometry"],
            index=0,
        )

        tripo_generation_options = {
            "model_version": tripo_model_version,
            "negative_prompt": tripo_negative_prompt or None,
            "face_limit": tripo_face_limit if tripo_face_limit > 0 else None,
            "texture": tripo_texture,
            "pbr": tripo_pbr,
            "quad": tripo_quad,
            "smart_low_poly": tripo_smart_low_poly,
            "auto_size": tripo_auto_size,
            "enable_image_autofix": tripo_enable_image_autofix,
            "generate_parts": tripo_generate_parts,
            "export_uv": tripo_export_uv,
            "texture_quality": tripo_texture_quality or None,
            "geometry_quality": tripo_geometry_quality or None,
            "texture_alignment": tripo_texture_alignment or None,
            "orientation": tripo_orientation or None,
            "compress": tripo_compress or None,
        }
    else:
        st.markdown(
            "<div style='padding:14px 16px; background:#f7f5f2; border-radius:12px; color:#6b6560; font-size:0.9rem;'>当前引擎暂无高级参数可配置</div>",
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# ===================== Step 4: 生成按钮 =====================
generate_btn = st.button(
    "🚀 开始生成",
    type="primary",
    disabled=not effective_available_providers,
    use_container_width=True,
)

_init_generation_state()
for running_task_id in list_running_task_ids():
    _add_active_task(running_task_id)

if generate_btn:
    if input_type == "上传图片" and not image_data:
        st.error("请先上传图片")
    elif input_type == "输入文本" and not text_input:
        st.error("请先输入物品描述")
    else:
        with st.spinner("正在提交生成任务..."):
            effective_category = selected_category
            effective_tags = selected_tags
            effective_input_text = text_input if input_type == "输入文本" else ""

            if input_type == "输入文本":
                route_result = enhance_and_route_text(effective_input_text, use_llm=True)
                effective_input_text = route_result.enhanced_prompt or effective_input_text
                effective_category = route_result.category
                effective_tags = route_result.tags
                st.info(
                    "文本路由已生效: "
                    f"{CATEGORY_NAMES[effective_category]} / "
                    f"{', '.join([TAG_NAMES[t] for t in effective_tags]) if effective_tags else '无标签'} "
                    f"({route_result.source})"
                )

            task = generator.create_task(
                category=effective_category,
                secondary_tags=effective_tags,
                mode=selected_mode,
                input_type="image" if input_type == "上传图片" else "text",
                input_data=effective_input_text if input_type == "输入文本" else "",
                provider=selected_provider,
                available_providers=effective_available_providers,
            )

            if image_data:
                image_path = storage.save_image(image_data, task.task_id)
                task.input_file_path = image_path
                generator.db.update_record(
                    task_id=task.task_id,
                    input_file_path=image_path,
                )

            api_keys = get_user_api_keys()

            try:
                generation_options = (
                    sf3d_generation_options
                    if task.provider == APIProvider.SF3D
                    else hunyuan_generation_options
                    if task.provider == APIProvider.HUNYUAN
                    else tripo_generation_options
                    if task.provider == APIProvider.TRIPO
                    else None
                )

                started = start_generation_task(
                    task,
                    api_keys,
                    generation_options=generation_options,
                )
                _add_active_task(task.task_id)

                if started:
                    st.success(f"任务已提交到后台，可切换页面。任务ID: {task.task_id}")
                else:
                    st.info(f"任务已在后台运行中: {task.task_id}")

            except Exception as e:
                st.error(f"生成过程出错: {str(e)}")

st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

# ===================== Step 5: 任务结果区 =====================
result_tabs = st.tabs(["⏳ 进行中 / 最近任务", "🔍 任务查询"])

with result_tabs[0]:
    active_task_ids = st.session_state.active_generation_task_ids
    if not active_task_ids:
        st.info("暂无进行中的任务，提交生成后任务将显示在这里。")
    else:
        for active_task_id in active_task_ids:
            task = generator.get_task(active_task_id)
            if not task:
                continue

            worker_state = get_generation_task_state(active_task_id) or {}
            worker_status = worker_state.get("status")

            if task.status in ["pending", "processing"] or worker_status == "running":
                st.markdown(
                    f"""
                    <div class="task-card-custom">
                        <div class="task-header-custom">
                            <span class="task-id-label">{task.task_id}</span>
                            <span class="status-badge status-running">生成中</span>
                        </div>
                        <div style="font-size:0.9rem; color:#5a5550;">
                            {CATEGORY_NAMES.get(task.category, task.category.value)} · {task.mode.value} · {task.provider.value}
                        </div>
                        <div style="font-size:0.85rem; color:#9a9590; margin-top:6px;">任务正在后台运行，可放心切换页面。</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                continue

            if task.status == "completed":
                st.markdown(
                    f"""
                    <div class="task-card-custom">
                        <div class="task-header-custom">
                            <span class="task-id-label">{task.task_id}</span>
                            <span class="status-badge status-success">已完成</span>
                        </div>
                        <div style="font-size:0.9rem; color:#5a5550;">
                            {CATEGORY_NAMES.get(task.category, task.category.value)} · {task.mode.value} · {task.provider.value}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                dl_col1, dl_col2 = st.columns([1, 4])
                with dl_col1:
                    if task.model_url:
                        st.link_button("⬇️ 下载模型", task.model_url, use_container_width=True)
                if task.model_file_path:
                    show_3d_model(task.model_file_path)
                continue

            if task.status == "failed":
                st.markdown(
                    f"""
                    <div class="task-card-custom">
                        <div class="task-header-custom">
                            <span class="task-id-label">{task.task_id}</span>
                            <span class="status-badge status-error">失败</span>
                        </div>
                        <div style="font-size:0.9rem; color:#8a4a4a;">{task.error_message or 'Unknown error'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

with result_tabs[1]:
    task_id_input = st.text_input("输入任务ID查询状态", placeholder="例如：task_abc123")
    if task_id_input:
        task = generator.get_task(task_id_input)
        if task:
            meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
            with meta_col1:
                st.metric("物品分类", CATEGORY_NAMES[task.category])
            with meta_col2:
                st.metric("生成模式", task.mode.value)
            with meta_col3:
                st.metric("API 引擎", task.provider.value)
            with meta_col4:
                st.metric("任务状态", task.status)

            if task.secondary_tags:
                tag_badge_html = " ".join([f'<span class="badge badge-purple">{TAG_NAMES[t]}</span>' for t in task.secondary_tags])
                st.markdown(f"<div style='margin-top:8px; margin-bottom:12px;'>**二级标签**：{tag_badge_html}</div>", unsafe_allow_html=True)

            st.json({
                "task_id": task.task_id,
                "category": CATEGORY_NAMES[task.category],
                "tags": [TAG_NAMES[t] for t in task.secondary_tags],
                "mode": task.mode.value,
                "provider": task.provider.value,
                "status": task.status,
                "model_url": task.model_url,
                "created_at": str(task.created_at),
            })

            if task.model_file_path:
                st.markdown(f"**本地模型**：`{task.model_file_path}`")
                show_3d_model(task.model_file_path)
        else:
            st.warning("未找到该任务")

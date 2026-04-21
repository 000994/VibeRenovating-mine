import asyncio
import base64
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
import streamlit as st
import streamlit.components.v1 as components

from api import GenerationStatus
from api.hunyuan import HunyuanAPI
from config import APIProvider, CATEGORY_NAMES
from core.generator import Generator
from models.database import Database
from utils.storage import StorageManager
from assets.style import inject_custom_css


db = Database()
generator = Generator(db=db)
storage = StorageManager()

st.set_page_config(
    page_title="历史记录",
    page_icon="📜",
    layout="wide",
)

inject_custom_css()

st.title("📜 生成历史记录")


def show_3d_model(model_path: str):
    path = Path(model_path)
    if not path.exists():
        st.warning(f"模型文件不存在: {model_path}")
        return

    with open(path, "rb") as f:
        model_data = f.read()

    model_base64 = base64.b64encode(model_data).decode()
    html_code = f"""
    <div style=\"width: 100%; height: 400px; position: relative;\">
      <model-viewer
        src=\"data:model/gltf-binary;base64,{model_base64}\"
        alt=\"3D Model\"
        auto-camera-controls
        camera-controls
        touch-action=\"pan-y\"
        style=\"width: 100%; height: 100%; background-color: #f7f5f2;\"
        shadow-intensity=\"1\"
        environment-image=\"neutral\"
      ></model-viewer>
    </div>
    <script type=\"module\">
      import 'https://ajax.googleapis.com/ajax/libs/model-viewer/3.0.1/model-viewer.min.js';
    </script>
    """
    components.html(html_code, height=420)


def show_preview_media(preview_src: str, preview_type: str = "image"):
    if not preview_src:
        return

    if preview_type == "video":
        video_html = f"""
        <video width=\"100%\" height=\"300\" controls autoplay loop muted>
            <source src=\"{preview_src}\" type=\"video/mp4\">
            您的浏览器不支持视频播放
        </video>
        """
        components.html(video_html, height=340)
    else:
        try:
            st.image(preview_src, caption="预览图", use_container_width=True)
        except Exception:
            st.markdown(f"[查看预览图]({preview_src})")


def ensure_local_preview(task_id: str, preview_url: str) -> str:
    local_preview_path = storage.get_preview_path(task_id)
    if local_preview_path:
        return local_preview_path
    if not preview_url:
        return ""
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(preview_url)
            response.raise_for_status()
            return storage.save_preview(
                response.content,
                task_id=task_id,
                source_url=preview_url,
                content_type=response.headers.get("Content-Type", ""),
            )
    except Exception:
        return ""


async def query_hunyuan_status(task_id: str, job_id: str, secret_id: str, secret_key: str):
    api = HunyuanAPI(secret_id, secret_key=secret_key)
    result = await api.get_status(task_id, job_id)
    await api.close()
    return result


st.markdown(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div style="color:#6b6560; font-size:0.9rem;">最后更新: {datetime.now().strftime('%H:%M:%S')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===================== 筛选栏 & 存储统计 =====================
st.markdown("<div class='card-title' style='font-size:1.1rem; margin-bottom:12px;'>🔍 筛选与统计</div>", unsafe_allow_html=True)

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    category_filter = st.selectbox("物品分类", ["全部"] + list(CATEGORY_NAMES.values()))
with filter_col2:
    provider_filter = st.selectbox("API提供商", ["全部"] + [p.value for p in APIProvider])
with filter_col3:
    status_filter = st.selectbox("状态", ["全部", "pending", "processing", "completed", "failed"])
with filter_col4:
    limit = st.slider("显示数量", 10, 100, 50)

stats = storage.get_storage_stats()
stat_col1, stat_col2, stat_col3 = st.columns(3)
with stat_col1:
    st.metric("模型数量", stats["models_count"])
with stat_col2:
    st.metric("图片数量", stats["images_count"])
with stat_col3:
    st.metric("总存储", f"{stats['total_size_mb']:.2f} MB")

st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

if st.button("🔄 刷新记录", type="primary", use_container_width=True):
    st.rerun()

cat_enum = None
if category_filter != "全部":
    for cat, name in CATEGORY_NAMES.items():
        if name == category_filter:
            cat_enum = cat
            break

prov_enum = None
if provider_filter != "全部":
    try:
        prov_enum = APIProvider(provider_filter)
    except ValueError:
        pass

tasks = generator.get_tasks(
    category=cat_enum,
    provider=prov_enum,
    status=status_filter if status_filter != "全部" else None,
    limit=limit,
)

if not tasks:
    st.info("暂无历史记录")
else:
    st.markdown(f"共找到 **{len(tasks)}** 条记录")

    for task in tasks:
        status_badge_class = {
            "pending": "badge-orange",
            "processing": "badge-blue",
            "completed": "badge-green",
            "failed": "badge-red",
        }.get(task.status, "badge-gray")
        status_text = {
            "pending": "待处理",
            "processing": "生成中",
            "completed": "已完成",
            "failed": "失败",
        }.get(task.status, task.status)

        # 拼装 task-meta 内容，避免条件不满足时产生空行导致 Markdown 解析异常
        meta_items = [
            f'<div class="task-meta-item"><strong>分类:</strong> {CATEGORY_NAMES.get(task.category, task.category.value)}</div>',
            f'<div class="task-meta-item"><strong>模式:</strong> {task.mode.value}</div>',
            f'<div class="task-meta-item"><strong>API:</strong> {task.provider.value}</div>',
            f'<div class="task-meta-item"><strong>创建时间:</strong> {task.created_at.strftime("%Y-%m-%d %H:%M")}</div>',
        ]
        if task.completed_at:
            meta_items.append(
                f'<div class="task-meta-item"><strong>完成时间:</strong> {task.completed_at.strftime("%Y-%m-%d %H:%M")}</div>'
            )
        if task.job_id:
            meta_items.append(
                f'<div class="task-meta-item"><strong>JobId:</strong> {task.job_id}</div>'
            )
        task_meta_html = "\n".join(meta_items)

        with st.container():
            st.markdown(
                f"""
                <div class="task-card">
                    <div class="task-header">
                        <div style="font-weight:600; color:#2d2a26;">{task.task_id[:16]}...</div>
                        <span class="badge {status_badge_class}">{status_text}</span>
                    </div>
                    <div class="task-meta">
                        {task_meta_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if task.error_message:
                st.error(f"错误信息: {task.error_message}")

            local_preview_path = ensure_local_preview(task.task_id, task.preview_url or "")

            inner_cols = st.columns([1, 1, 1, 1])
            with inner_cols[0]:
                if task.model_file_path:
                    try:
                        with open(task.model_file_path, "rb") as f:
                            st.download_button(
                                "⬇️ 下载模型",
                                f,
                                file_name=f"{task.task_id}.glb",
                                mime="model/gltf-binary",
                                key=f"model_dl_{task.task_id}",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.warning(f"无法读取模型文件: {e}")
                elif task.model_url:
                    st.link_button("⬇️ 下载模型", task.model_url, use_container_width=True)
                else:
                    st.empty()

            with inner_cols[1]:
                if local_preview_path:
                    try:
                        with open(local_preview_path, "rb") as f:
                            suffix = Path(local_preview_path).suffix.lower()
                            mime = "video/mp4" if suffix in {".mp4", ".webm"} else "image/png"
                            st.download_button(
                                "⬇️ 下载预览",
                                f,
                                file_name=Path(local_preview_path).name,
                                mime=mime,
                                key=f"preview_dl_{task.task_id}",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.warning(f"无法读取预览文件: {e}")
                elif task.preview_url:
                    st.link_button("⬇️ 下载预览", task.preview_url, use_container_width=True)
                else:
                    st.empty()

            with inner_cols[2]:
                if task.status in ["pending", "processing"] and task.provider.value == "hunyuan" and task.job_id:
                    if st.button("🔍 查询状态", key=f"query_{task.task_id}", use_container_width=True):
                        with st.spinner("正在查询..."):
                            try:
                                api_keys = db.get_all_api_keys()
                                key_info = api_keys.get("hunyuan")
                                if not key_info:
                                    st.warning("未配置混元 API Key，请在设置页填写 SecretId/SecretKey")
                                else:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    result = loop.run_until_complete(
                                        query_hunyuan_status(
                                            task.task_id,
                                            task.job_id,
                                            key_info.get("api_key"),
                                            key_info.get("secret_key"),
                                        )
                                    )
                                    loop.close()

                                    if result.status == GenerationStatus.COMPLETED:
                                        db.update_record(
                                            task_id=task.task_id,
                                            status="completed",
                                            model_url=result.model_url or "",
                                            preview_url=result.preview_url or "",
                                        )
                                        st.success("任务已完成")
                                        st.rerun()
                                    elif result.status == GenerationStatus.PROCESSING:
                                        st.info("任务仍在处理中，请稍后再试")
                                    else:
                                        db.update_record(
                                            task_id=task.task_id,
                                            status="failed",
                                            error_message=result.error_message or "Unknown error",
                                        )
                                        st.error(f"任务失败: {result.error_message}")
                                        st.rerun()
                            except Exception as e:
                                st.error(f"查询失败: {e}")
                else:
                    st.empty()

            with inner_cols[3]:
                if st.button("🗑️ 删除", key=f"del_{task.task_id}", use_container_width=True):
                    generator.delete_task(task.task_id)
                    st.success("已删除")
                    st.rerun()

            if local_preview_path or task.preview_url:
                st.markdown("**预览**:")
                if local_preview_path:
                    local_suffix = Path(local_preview_path).suffix.lower()
                    if local_suffix in {".mp4", ".webm"}:
                        show_preview_media(local_preview_path, "video")
                    else:
                        st.image(local_preview_path, caption="预览图", use_container_width=True)
                else:
                    preview_url = task.preview_url
                    preview_path = urlparse(preview_url).path.lower()
                    if preview_path.endswith(".mp4") or preview_path.endswith(".webm"):
                        show_preview_media(preview_url, "video")
                    else:
                        show_preview_media(preview_url, "image")

            if task.model_file_path:
                st.markdown("**3D 预览**:")
                show_3d_model(task.model_file_path)

            st.markdown("<div style='margin-bottom:24px;'></div>", unsafe_allow_html=True)

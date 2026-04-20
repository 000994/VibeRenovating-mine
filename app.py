import streamlit as st
import streamlit.components.v1 as components

from config import CATEGORY_EXAMPLES
from core.classifier import get_all_categories, get_all_tags
from assets.style import inject_custom_css, hero_section

st.set_page_config(
    page_title="VibeRenovating - 3D生成平台",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()

# 全局侧边栏 Logo 与信息（所有页面共享）
st.logo(image="🏡", size="large")

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:12px;">
            <div style="font-size:1.15rem; font-weight:700; color:#2d2a26; letter-spacing:-0.3px;">VibeRenovating</div>
            <div style="font-size:0.75rem; color:#9a9590; margin-top:2px;">智能 3D 模型生成平台</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="sidebar-footer">
            切换页面以查看历史记录或设置
        </div>
        """,
        unsafe_allow_html=True,
    )


def _force_scroll_top() -> None:
    components.html(
        """
        <script>
          try {
            history.scrollRestoration = "manual";
          } catch (e) {}
          window.scrollTo(0, 0);
          if (window.parent) {
            window.parent.scrollTo(0, 0);
          }
          document.documentElement.scrollTop = 0;
          document.body.scrollTop = 0;
        </script>
        """,
        height=0,
    )


def _render_main_page() -> None:
    _force_scroll_top()

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: block !important; }
        [data-testid="collapsedControl"] { display: flex !important; }
        [data-testid="stHeader"] { display: block !important; }
        .main .block-container,
        [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewBlockContainer"] {
            max-width: 1200px !important;
            margin: auto !important;
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    hero_section("🏡 VibeRenovating", "智能 3D 模型生成平台 · 集成多种生成引擎 · 自动推荐最优方案")

    # 平台简介卡片
    st.markdown(
        """
        <div class="card">
            <div class="card-title">📖 平台简介</div>
            <div class="card-subtitle">
                VibeRenovating 是一个集成多种 3D 生成 API 的智能平台，
                会根据物品特征自动推荐更合适的生成引擎，让 3D 内容创作更简单高效。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 支持的 API
    st.subheader("🚀 支持的生成引擎")
    api_items = [
        ("⚡", "SF3D", "极快生成，适合快速预览", "badge-blue"),
        ("🎨", "Meshy", "支持文生 3D 和图生 3D", "badge-purple"),
        ("🏗️", "Rodin", "适合框架类与复杂结构", "badge-green"),
        ("🌄", "混元3D", "适合场景类与复杂背景", "badge-orange"),
        ("🚀", "Tripo", "生成效率高，适合快速试错", "badge-blue"),
    ]
    cols = st.columns(len(api_items))
    for col, (icon, name, desc, badge_cls) in zip(cols, api_items):
        with col:
            st.markdown(
                f"""
                <div style="text-align:center; padding:16px; background:white; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.04); margin-bottom:12px;">
                    <div style="font-size:2rem; margin-bottom:6px;">{icon}</div>
                    <div style="font-weight:600; color:#2d2a26; margin-bottom:4px;">{name}</div>
                    <div style="font-size:0.8rem; color:#6b6560;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 物品分类
    st.subheader("📦 物品分类")
    cat_cols = st.columns(2)
    categories = list(get_all_categories())
    for idx, (cat, name) in enumerate(categories):
        examples = CATEGORY_EXAMPLES.get(cat, "")
        with cat_cols[idx % 2]:
            st.markdown(
                f"""
                <div style="padding:14px 18px; background:white; border-radius:12px; margin-bottom:10px; box-shadow:0 1px 6px rgba(0,0,0,0.03); border-left:4px solid #c87e5a;">
                    <div style="font-weight:600; color:#2d2a26;">{name}</div>
                    <div style="font-size:0.85rem; color:#6b6560; margin-top:4px;">{examples}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 二级标签
    st.subheader("🏷️ 二级标签")
    tags = get_all_tags()
    tag_badges = " ".join(
        [f'<span class="badge badge-purple" style="margin:4px;">{name}</span>' for _, name in tags]
    )
    st.markdown(
        f"""
        <div class="card">
            <div class="card-subtitle" style="margin-bottom:0;">
                根据物品特征选择标签，系统会进一步优化 API 推荐。
            </div>
            <div style="margin-top:12px;">{tag_badges}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 生成模式
    st.subheader("⚙️ 生成模式")
    mode_cols = st.columns(2)
    with mode_cols[0]:
        st.markdown(
            """
            <div style="text-align:center; padding:18px; background:white; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.04);">
                <div style="font-size:1.5rem; margin-bottom:6px;">⚡</div>
                <div style="font-weight:600; color:#2d2a26;">快速预览</div>
                <div style="font-size:0.85rem; color:#6b6560;">先看结构与大体效果</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mode_cols[1]:
        st.markdown(
            """
            <div style="text-align:center; padding:18px; background:white; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.04);">
                <div style="font-size:1.5rem; margin-bottom:6px;">💎</div>
                <div style="font-weight:600; color:#2d2a26;">精细生成</div>
                <div style="font-size:0.85rem; color:#6b6560;">用于更高质量的最终模型</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 使用流程
    st.subheader("🛠️ 使用流程")
    steps = [
        "进入「设置」页填写 API Key",
        "进入「生成」页上传图片或输入文本",
        "选择物品分类和标签",
        "选择生成模式并提交",
        "在「历史记录」中查看结果并下载模型",
    ]
    for i, step in enumerate(steps, 1):
        st.markdown(
            f"""
            <div class="step-item">
                <div class="step-number">{i}</div>
                <div class="step-text">{step}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


_render_main_page()

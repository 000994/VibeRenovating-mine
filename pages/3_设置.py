import streamlit as st

from config import APIProvider
from models.database import Database
from assets.style import inject_custom_css


db = Database()

st.set_page_config(
    page_title="API 设置",
    page_icon="⚙️",
    layout="wide",
)

inject_custom_css()

st.title("⚙️ API 密钥设置")

st.markdown(
    """
    <div class="card">
        <div class="card-title">🔐 密钥配置说明</div>
        <div class="card-subtitle">
            配置您的 3D 生成 API 密钥。密钥会保存在本地 SQLite 数据库，不会上报到任何第三方服务。
        </div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin-top:10px;">
            <div style="font-size:0.85rem; color:#5a5550;">⚡ <a href="https://platform.stability.ai" target="_blank">SF3D</a></div>
            <div style="font-size:0.85rem; color:#5a5550;">🎨 <a href="https://docs.meshy.ai" target="_blank">Meshy</a></div>
            <div style="font-size:0.85rem; color:#5a5550;">🏗️ <a href="https://hyperhuman.deemos.com" target="_blank">Rodin</a></div>
            <div style="font-size:0.85rem; color:#5a5550;">🌄 <a href="https://console.cloud.tencent.com/hunyuan/start" target="_blank">混元生3D</a></div>
            <div style="font-size:0.85rem; color:#5a5550;">🚀 <a href="https://www.tripo3d.ai" target="_blank">Tripo</a></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

api_configs = [
    {
        "provider": APIProvider.SF3D,
        "name": "SF3D (Stability AI)",
        "description": "极速生成，适合快速预览",
        "needs_secret": False,
        "key_label": "API Key",
        "key_placeholder": "sk-...",
    },
    {
        "provider": APIProvider.MESHY,
        "name": "Meshy",
        "description": "支持文生3D和图生3D",
        "needs_secret": False,
        "key_label": "API Key",
        "key_placeholder": "msy_xxx...",
    },
    {
        "provider": APIProvider.RODIN,
        "name": "Rodin (HyperHuman)",
        "description": "框架类表现更好，适合细长支撑结构",
        "needs_secret": False,
        "key_label": "API Key",
        "key_placeholder": "输入您的 API Key",
    },
    {
        "provider": APIProvider.HUNYUAN,
        "name": "混元生3D (腾讯云)",
        "description": "腾讯云 TC3 鉴权：填写 SecretId 和 SecretKey；若为临时凭证，可在 SecretKey 后追加 |Token",
        "needs_secret": True,
        "key_label": "SecretId",
        "secret_label": "SecretKey",
        "key_placeholder": "AKID...",
        "secret_placeholder": "输入 SecretKey（临时凭证可填 SecretKey|Token）",
    },
    {
        "provider": APIProvider.TRIPO,
        "name": "Tripo",
        "description": "快速生成，适合多轮试错",
        "needs_secret": False,
        "key_label": "API Key",
        "key_placeholder": "输入您的 API Key",
    },
]

current_keys = db.get_all_api_keys()

for config in api_configs:
    provider = config["provider"]
    current = current_keys.get(provider.value, {})
    has_key = bool(current.get("api_key"))
    has_secret = bool(current.get("secret_key"))

    status_html = ""
    if has_key:
        if config["needs_secret"]:
            if has_secret:
                status_html = f'<span class="badge badge-green">已配置</span>'
            else:
                status_html = '<span class="badge badge-orange">配置不完整</span>'
        else:
            status_html = '<span class="badge badge-green">已配置</span>'
    else:
        status_html = '<span class="badge badge-gray">未配置</span>'

    with st.container():
        st.markdown(
            f"""
            <div class="card" style="padding:20px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div style="font-weight:600; color:#2d2a26; font-size:1.05rem;">🗝️ {config['name']}</div>
                    {status_html}
                </div>
                <div style="font-size:0.9rem; color:#6b6560; margin-bottom:14px;">{config['description']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if has_key:
            if config["needs_secret"]:
                if has_secret:
                    st.success(
                        f"已配置 ({config.get('key_label', 'API Key')}: {current['api_key'][:8]}..., "
                        f"{config.get('secret_label', 'Secret Key')}: {current['secret_key'][:6]}...)"
                    )
                else:
                    st.warning("检测到仅保存了 SecretId，缺少 SecretKey，请重新保存。")
            else:
                st.success(f"已配置 ({config.get('key_label', 'API Key')}: {current['api_key'][:8]}...)")

        col1, col2 = st.columns(2)

        with col1:
            api_key = st.text_input(
                config.get("key_label", "API Key"),
                value="",
                placeholder=config["key_placeholder"],
                type="password",
                key=f"key_{provider.value}",
            )

        if config["needs_secret"]:
            with col2:
                secret_key = st.text_input(
                    config.get("secret_label", "Secret Key"),
                    value="",
                    placeholder=config["secret_placeholder"],
                    type="password",
                    key=f"secret_{provider.value}",
                )
        else:
            secret_key = None

        btn_cols = st.columns([1, 1, 4])
        with btn_cols[0]:
            if st.button("💾 保存", key=f"save_{provider.value}", use_container_width=True):
                api_key = (api_key or "").strip()
                secret_key = (secret_key or "").strip() if secret_key is not None else None
                if api_key:
                    if config["needs_secret"] and not secret_key:
                        st.warning(f"请输入 {config.get('secret_label', 'Secret Key')}")
                    else:
                        db.save_api_key(provider.value, api_key, secret_key)
                        st.success("保存成功")
                        st.rerun()
                else:
                    st.warning(f"请输入 {config.get('key_label', 'API Key')}")

        with btn_cols[1]:
            if has_key:
                if st.button("🗑️ 删除", key=f"del_{provider.value}", use_container_width=True):
                    session = db.get_session()
                    from models.database import UserAPIKey

                    record = session.query(UserAPIKey).filter_by(provider=provider.value).first()
                    if record:
                        session.delete(record)
                        session.commit()
                    session.close()
                    st.success("已删除")
                    st.rerun()

        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div class='card-title' style='font-size:1.2rem; margin-bottom:12px;'>📊 当前配置状态</div>", unsafe_allow_html=True)

status_cells = []
for provider in APIProvider:
    current = current_keys.get(provider.value, {})
    configured = bool(current.get("api_key"))
    if provider == APIProvider.HUNYUAN:
        configured = bool(current.get("api_key")) and bool(current.get("secret_key"))
    badge = '<span class="badge badge-green">已配置</span>' if configured else '<span class="badge badge-gray">未配置</span>'
    status_cells.append(
        f"""
        <div class="status-cell">
            <div class="status-label">{provider.value.upper()}</div>
            <div class="status-value" style="margin-top:6px;">{badge}</div>
        </div>
        """
    )

st.html(
    f'<div class="status-grid">{ "".join(status_cells) }</div>'
)

st.markdown(
    """
    <div class="card" style="margin-top:20px;">
        <div class="card-title">🔒 安全提示</div>
        <ul style="margin-bottom:0; color:#5a5550; font-size:0.9rem;">
            <li>密钥保存在本地 SQLite 数据库，不会上报到第三方服务。</li>
            <li>混元生3D 使用腾讯云 TC3 鉴权，请妥善保管 SecretId / SecretKey。</li>
            <li>如使用临时凭证（STS），建议在后续扩展 Token 输入项。</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

import streamlit as st


def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', "PingFang SC", "Microsoft YaHei", sans-serif;
        }

        /* 主背景 - 温暖米白 */
        .stApp {
            background: #faf8f5;
        }

        /* 标题样式 - 去掉渐变，用温暖深色 */
        h1 {
            color: #2d2a26 !important;
            font-weight: 700 !important;
            letter-spacing: -0.3px;
        }

        h2, h3 {
            color: #2d2a26 !important;
            font-weight: 600 !important;
        }

        /* 卡片容器 - 更柔和的阴影和边框 */
        .card {
            background: #ffffff;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(45, 42, 38, 0.04);
            border: 1px solid #e8e4df;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .card:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(45, 42, 38, 0.08);
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #2d2a26;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-subtitle {
            font-size: 0.9rem;
            color: #6b6560;
            margin-bottom: 16px;
        }

        /* Hero 区域 - 温暖柔和的奶油色 */
        .hero {
            background: linear-gradient(135deg, #f5f0e8 0%, #ede6db 100%);
            border-radius: 20px;
            padding: 40px 32px;
            color: #2d2a26;
            margin-bottom: 32px;
            text-align: center;
            border: 1px solid #e8e4df;
            box-shadow: 0 2px 10px rgba(45, 42, 38, 0.04);
        }

        .hero h1 {
            -webkit-text-fill-color: #2d2a26 !important;
            color: #2d2a26 !important;
            font-size: 2.4rem !important;
            margin-bottom: 12px;
        }

        .hero p {
            font-size: 1.1rem;
            color: #6b6560;
            max-width: 600px;
            margin: 0 auto;
        }

        /* 特性网格 */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }

        .feature-item {
            background: #ffffff;
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(45, 42, 38, 0.04);
            border: 1px solid #e8e4df;
        }

        .feature-icon {
            font-size: 2rem;
            margin-bottom: 8px;
        }

        .feature-name {
            font-weight: 600;
            color: #2d2a26;
            margin-bottom: 4px;
        }

        .feature-desc {
            font-size: 0.85rem;
            color: #6b6560;
        }

        /* Badge - 温暖低饱和 */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .badge-blue {
            background: #e8e8e8;
            color: #5a5a5a;
        }

        .badge-green {
            background: #e3efe3;
            color: #4a6b4a;
        }

        .badge-purple {
            background: #ede6db;
            color: #7a6b5a;
        }

        .badge-orange {
            background: #f5e6d8;
            color: #8a5a3a;
        }

        .badge-red {
            background: #f5e0e0;
            color: #8a4a4a;
        }

        .badge-gray {
            background: #f0eeeb;
            color: #5a5550;
        }

        .badge-terracotta {
            background: #f5e6d8;
            color: #8a5a3a;
        }

        .badge-sage {
            background: #e3efe3;
            color: #4a6b4a;
        }

        /* 步骤 */
        .step-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin: 16px 0;
        }

        .step-item {
            display: flex;
            align-items: center;
            gap: 14px;
            background: #ffffff;
            padding: 14px 18px;
            border-radius: 12px;
            box-shadow: 0 1px 4px rgba(45, 42, 38, 0.03);
            border: 1px solid #e8e4df;
        }

        .step-number {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #c87e5a;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
            flex-shrink: 0;
        }

        .step-text {
            color: #4a4540;
            font-size: 0.95rem;
        }

        /* ================== 侧边栏深度美化 ================== */
        [data-testid="stSidebar"] {
            background: #f7f5f2 !important;
            border-right: 1px solid #e8e4df;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* 侧边栏标题/Logo区域 */
        .sidebar-logo {
            text-align: center;
            padding: 12px 8px 20px 8px;
            margin-bottom: 8px;
            border-bottom: 1px solid #e8e4df;
        }
        .sidebar-logo-icon {
            font-size: 2rem;
            margin-bottom: 4px;
        }
        .sidebar-logo-text {
            font-size: 1.15rem;
            font-weight: 700;
            color: #2d2a26;
            letter-spacing: -0.3px;
        }
        .sidebar-logo-sub {
            font-size: 0.75rem;
            color: #9a9590;
            margin-top: 2px;
        }

        /* 侧边栏导航项美化 */
        [data-testid="stSidebarNav"] {
            background: transparent !important;
        }
        [data-testid="stSidebarNav"] ul {
            padding-left: 0 !important;
            list-style: none !important;
        }
        [data-testid="stSidebarNav"] li {
            margin-bottom: 6px !important;
        }
        [data-testid="stSidebarNav"] a {
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            padding: 10px 14px !important;
            border-radius: 12px !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
            color: #6b6560 !important;
            text-decoration: none !important;
            transition: all 0.2s ease !important;
            border: 1px solid transparent !important;
        }
        [data-testid="stSidebarNav"] a:hover {
            background: #ffffff !important;
            color: #2d2a26 !important;
            border-color: #e8e4df !important;
            box-shadow: 0 2px 8px rgba(45,42,38,0.04) !important;
        }
        /* 当前选中页面高亮 */
        [data-testid="stSidebarNav"] a[data-active="true"],
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: #ffffff !important;
            color: #c87e5a !important;
            border-color: #e8d4c8 !important;
            box-shadow: 0 2px 8px rgba(200,126,90,0.10) !important;
            font-weight: 600 !important;
        }
        /* 隐藏侧边栏默认的 page 图标，用 emoji 替代在页面标题里 */
        [data-testid="stSidebarNav"] img {
            display: none !important;
        }

        /* 侧边栏底部信息 */
        .sidebar-footer {
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #e8e4df;
            text-align: center;
            font-size: 0.75rem;
            color: #9a9590;
        }

        /* ================== 步骤条 ================== */
        .step-bar {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 24px;
            padding: 14px 18px;
            background: #ffffff;
            border-radius: 14px;
            border: 1px solid #e8e4df;
            box-shadow: 0 1px 4px rgba(45,42,38,0.03);
        }
        .step-bar-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            font-weight: 500;
            color: #9a9590;
        }
        .step-bar-item.active {
            color: #c87e5a;
            font-weight: 600;
        }
        .step-bar-item.done {
            color: #4a6b4a;
        }
        .step-bar-num {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #f0eeeb;
            color: #9a9590;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
            flex-shrink: 0;
        }
        .step-bar-item.active .step-bar-num {
            background: #c87e5a;
            color: #ffffff;
        }
        .step-bar-item.done .step-bar-num {
            background: #e3efe3;
            color: #4a6b4a;
        }
        .step-bar-arrow {
            color: #d8d4cf;
            font-size: 0.8rem;
        }

        /* ================== 轻量卡片 ================== */
        .lite-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 18px;
            border: 1px solid #e8e4df;
            box-shadow: 0 1px 4px rgba(45,42,38,0.03);
        }
        .lite-card-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: #2d2a26;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* 紧凑行 */
        .compact-row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .compact-row > div {
            flex: 1;
            min-width: 200px;
        }

        /* 模式选择卡片 - 更紧凑 */
        .mode-select-card {
            border: 2px solid #e8e4df;
            border-radius: 12px;
            padding: 14px 12px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: #ffffff;
        }
        .mode-select-card:hover {
            border-color: #d8d4cf;
            background: #fdfcfa;
        }
        .mode-select-card.active {
            border-color: #c87e5a;
            background: #fdf8f4;
        }
        .mode-select-icon {
            font-size: 1.4rem;
            margin-bottom: 4px;
        }
        .mode-select-name {
            font-weight: 600;
            color: #2d2a26;
            font-size: 0.9rem;
        }
        .mode-select-desc {
            font-size: 0.75rem;
            color: #9a9590;
            margin-top: 2px;
        }

        /* 推荐标签 */
        .recommend-chip {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: #f5f0e8;
            color: #7a6b5a;
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 0.8rem;
            font-weight: 500;
            margin: 2px;
        }

        /* 信息提示条 */
        .info-strip {
            background: #f5f0e8;
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 0.85rem;
            color: #7a6b5a;
            border: 1px solid #e8e4df;
        }

        /* 隐藏 streamlit 默认 radio 的圆点（用于模式选择时） */
        .stRadio > div[role="radiogroup"] {
            display: flex;
            gap: 10px;
        }
        .stRadio > div[role="radiogroup"] > label {
            flex: 1;
        }
        .stRadio > div[role="radiogroup"] > label > div:first-child {
            display: none;
        }

        /* 按钮美化 - 通用 */
        .stButton > button {
            border-radius: 10px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }

        /* Primary 按钮 - 暖陶土色 */
        .stButton > button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            background-color: #c87e5a !important;
            color: #ffffff !important;
            border: none !important;
        }

        .stButton > button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(200, 126, 90, 0.25) !important;
            background-color: #b56d4a !important;
        }

        .stButton > button[kind="primary"]:active,
        button[data-testid="baseButton-primary"]:active {
            background-color: #a05d3d !important;
        }

        /* Secondary 按钮 - 柔和边框 */
        .stButton > button[kind="secondary"],
        button[data-testid="baseButton-secondary"] {
            background-color: #ffffff !important;
            color: #2d2a26 !important;
            border: 1px solid #e8e4df !important;
        }

        .stButton > button[kind="secondary"]:hover,
        button[data-testid="baseButton-secondary"]:hover {
            background-color: #f7f5f2 !important;
            border-color: #d8d4cf !important;
        }

        /* Expander 美化 */
        .streamlit-expanderHeader {
            background: #ffffff !important;
            border-radius: 12px !important;
            font-weight: 500 !important;
            border: 1px solid #e8e4df !important;
        }

        /* 表格/状态表 */
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin: 16px 0;
        }

        .status-cell {
            background: #ffffff;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 1px 4px rgba(45, 42, 38, 0.03);
            border: 1px solid #e8e4df;
        }

        .status-label {
            font-size: 0.85rem;
            color: #6b6560;
            margin-bottom: 4px;
        }

        .status-value {
            font-size: 1rem;
            font-weight: 600;
            color: #2d2a26;
        }

        /* 任务卡片 */
        .task-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(45, 42, 38, 0.04);
            border: 1px solid #e8e4df;
        }

        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .task-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 8px;
            margin-bottom: 12px;
        }

        .task-meta-item {
            font-size: 0.9rem;
            color: #5a5550;
        }

        /* Metric 重写 */
        [data-testid="stMetric"] {
            background: #ffffff;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 4px rgba(45, 42, 38, 0.03);
            border: 1px solid #e8e4df;
        }

        [data-testid="stMetricLabel"] {
            font-weight: 500 !important;
            color: #6b6560 !important;
        }

        [data-testid="stMetricValue"] {
            font-weight: 700 !important;
            color: #2d2a26 !important;
        }

        /* 分割线 */
        hr {
            border: none;
            border-top: 1px solid #e8e4df;
            margin: 24px 0;
        }

        /* 隐藏默认顶部 */
        [data-testid="stHeader"] {
            background: transparent !important;
        }

        /* 筛选栏 */
        .filter-bar {
            background: #ffffff;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(45, 42, 38, 0.04);
            border: 1px solid #e8e4df;
        }

        /* 配置面板卡片 */
        .config-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(45, 42, 38, 0.04);
            border: 1px solid #e8e4df;
        }

        /* 紧凑的列间距 */
        [data-testid="column"] {
            gap: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero_section(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, content_html: str):
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{title}</div>
            {content_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

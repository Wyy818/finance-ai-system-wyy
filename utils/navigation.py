import importlib
import streamlit as st

NAV_CONFIG = {
    "数据处理": {
        "icon": "🧹",
        "color": "#4FC3F7",
        "pages": {
            "AI 智能清洗": "modules.module1.mod1_etl",
            "常规表格处理": "modules.module1.mod1_table_general_processor",
        },
    },
    "AI 异常分析": {
        "icon": "🧠",
        "color": "#BA68C8",
        "pages": {
            "异常检测": "modules.module2.mod2_analysis",
        },
    },
    "数据可视化": {
        "icon": "📊",
        "color": "#81C784",
        "pages": {
            "图表生成": "modules.module3.mod3_visualization",
        },
    },
}

SIDEBAR_CSS = """
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1117 0%, #1a1f2e 100%);
    }
    [data-testid="stSidebar"] .sidebar-brand {
        text-align: center;
        padding: 1.2rem 0.5rem 0.8rem;
    }
    [data-testid="stSidebar"] .sidebar-brand h1 {
        font-size: 1.35rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #4FC3F7, #BA68C8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stSidebar"] .sidebar-brand p {
        color: #8892a4;
        font-size: 0.78rem;
        margin: 0.25rem 0 0;
    }
    [data-testid="stSidebar"] .nav-divider {
        border: none;
        border-top: 1px solid #2d3548;
        margin: 0.6rem 0;
    }
    [data-testid="stSidebar"] .nav-section-title {
        color: #6b7a90;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.4rem 0.2rem 0.2rem;
    }
    [data-testid="stSidebar"] .nav-module-badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    [data-testid="stSidebar"] .sidebar-footer {
        color: #5c6678;
        font-size: 0.72rem;
        text-align: center;
        padding: 1rem 0 0.5rem;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] > label {
        font-weight: 600;
        color: #c5cdd9;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        padding: 0.35rem 0.5rem;
        margin-bottom: 0.25rem;
        border: 1px solid transparent;
        transition: all 0.2s;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        background: rgba(255,255,255,0.06);
        border-color: #2d3548;
    }
</style>
"""


def _render_brand():
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <h1>🚀 业财数据平台</h1>
            <p>Finance AI System</p>
        </div>
        <hr class="nav-divider">
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str]:
    """渲染侧边栏，返回 (module_name, page_name)。"""
    st.sidebar.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
    _render_brand()

    module_names = list(NAV_CONFIG.keys())
    if "nav_module" not in st.session_state or st.session_state.nav_module not in module_names:
        st.session_state.nav_module = module_names[0]

    st.sidebar.markdown('<p class="nav-section-title">功能模块</p>', unsafe_allow_html=True)
    prev_module = st.session_state.nav_module
    selected_module = st.sidebar.radio(
        "功能模块",
        module_names,
        index=module_names.index(st.session_state.nav_module),
        format_func=lambda m: f"{NAV_CONFIG[m]['icon']}  {m}",
        key="sidebar_module_radio",
        label_visibility="collapsed",
    )

    module_cfg = NAV_CONFIG[selected_module]
    page_names = list(module_cfg["pages"].keys())

    if prev_module != selected_module or st.session_state.get("nav_page") not in page_names:
        st.session_state.nav_page = page_names[0]
    st.session_state.nav_module = selected_module

    st.sidebar.markdown(
        f'<span class="nav-module-badge" style="background:{module_cfg["color"]}22;color:{module_cfg["color"]};">'
        f'{module_cfg["icon"]} {selected_module}</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<p class="nav-section-title">子页面</p>', unsafe_allow_html=True)

    selected_page = st.sidebar.radio(
        "子页面",
        page_names,
        index=page_names.index(st.session_state.nav_page),
        key=f"sidebar_page_radio_{selected_module}",
        label_visibility="collapsed",
    )
    st.session_state.nav_page = selected_page

    st.sidebar.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="sidebar-footer">v0.1 · 模块化架构</div>',
        unsafe_allow_html=True,
    )

    return selected_module, selected_page


def dispatch_page(module_name: str, page_name: str):
    """根据导航配置动态加载并运行对应子页面。"""
    module_path = NAV_CONFIG[module_name]["pages"][page_name]
    mod = importlib.import_module(module_path)
    mod.run()

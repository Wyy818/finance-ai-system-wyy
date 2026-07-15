import importlib
import streamlit as st

NAV_CONFIG = {
    "数据处理": {
        "icon": "🧹",
        "color": "#4FC3F7",
        "pages": {
            "AI 智能清洗": "modules.module1.mod1_etl",
            "常规表格处理": "modules.module1.mod1_table_general_processor",
            "自定义处理": "modules.module1.mod1_table_general_processor",
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
        background: linear-gradient(180deg, #e8e8e8 0%, #d0d0d0 100%);
    }
    [data-testid="stSidebar"] .sidebar-brand {
        text-align: center;
        padding: 0.2rem 0.5rem 0.6rem;
        width: 100%;
        box-sizing: border-box;
        margin-top: -0.5rem;
    }
    [data-testid="stSidebar"] .sidebar-brand h1 {
        font-size: 2.25rem;
        font-weight: 900;
        margin: 0;
        background: linear-gradient(135deg, #FF69B4, #DDA0DD, #9370DB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 0.08em;
        width: 100%;
        line-height: 1.3;
    }
    [data-testid="stSidebar"] .sidebar-brand p {
        color: #666666;
        font-size: 0.85rem;
        margin: 0.3rem 0 0;
        text-align: center;
    }
    [data-testid="stSidebar"] .nav-divider {
        border: none;
        border-top: 1px solid #cccccc;
        margin: 0.5rem 0;
    }
    [data-testid="stSidebar"] .sidebar-footer {
        color: #666666;
        font-size: 0.85rem;
        text-align: center;
        padding: 1rem 0 0.5rem;
        font-weight: 600;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: #f5f5f5;
        border: 1px solid #cccccc;
        border-radius: 8px;
        margin-bottom: 0.3rem;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        font-size: 1.1rem;
        font-weight: 700;
        color: #333333;
        padding: 0.6rem 0.8rem;
        cursor: pointer;
        text-align: left;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        background: #e0e0e0;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary::marker {
        font-size: 0.85rem;
        color: #888888;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button {
        width: 100%;
        text-align: left;
        padding: 0.45rem 1.5rem;
        margin: 0.1rem 0;
        border-radius: 6px;
        border: none;
        font-size: 0.98rem;
        font-weight: 400;
        transition: all 0.15s;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button[data-baseweb="secondary"] {
        background: #f5f5f5;
        color: #333333;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button[data-baseweb="secondary"]:hover {
        background: #e8e8e8;
        color: #1a1a1a;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button[data-baseweb="primary"] {
        background: linear-gradient(135deg, #ADD8E6, #87CEEB) !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button[data-baseweb="primary"] span,
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button[data-baseweb="primary"] span * {
        background: transparent !important;
        color: #1a1a1a !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button[data-baseweb="primary"]:hover {
        background: linear-gradient(135deg, #87CEEB, #5BB5E0) !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button[data-baseweb="primary"]:hover span,
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stButton"] button[data-baseweb="primary"]:hover span * {
        background: transparent !important;
        color: #ffffff !important;
    }

    [data-testid="stToolbar"] {
        display: none !important;
    }

    [data-testid="stSidebar"] button[data-testid^="stButton"] {
        background: transparent !important;
    }
    [data-testid="stSidebar"] button[data-testid^="stButton"] span {
        background: transparent !important;
    }
    [data-testid="stSidebar"] button[data-testid^="stButton"] span svg {
        display: none !important;
    }
    [data-testid="stSidebar"] [data-baseweb="button"] {
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stSidebar"] [data-baseweb="button"] span {
        background: transparent !important;
    }
    [data-testid="stSidebar"] [data-baseweb="button"][data-kind="primary"] {
        background: linear-gradient(135deg, #ADD8E6, #87CEEB) !important;
        color: #1a1a1a !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] [data-baseweb="button"][data-kind="primary"]:hover {
        background: linear-gradient(135deg, #87CEEB, #5BB5E0) !important;
        color: #ffffff !important;
    }
</style>
"""


def _render_brand():
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <h1>业财融合<br>多功能系统</h1>
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

    if "nav_page" not in st.session_state:
        st.session_state.nav_page = list(NAV_CONFIG[st.session_state.nav_module]["pages"].keys())[0]

    # 首次进入时默认展开当前模块
    for module_name in module_names:
        ek = f"nav_expander_{module_name}"
        if ek not in st.session_state:
            st.session_state[ek] = (module_name == st.session_state.nav_module)

    for module_name in module_names:
        module_cfg = NAV_CONFIG[module_name]
        page_names = list(module_cfg["pages"].keys())

        expander_key = f"nav_expander_{module_name}"
        expander_label = f"{module_cfg['icon']}  {module_name}"

        with st.sidebar.expander(expander_label, expanded=st.session_state.get(expander_key, False)):
            for page_name in page_names:
                is_page_selected = st.session_state.get("nav_page") == page_name
                btn_key = f"nav_page_{module_name}_{page_name}"

                if st.button(
                    page_name,
                    key=btn_key,
                    help=page_name,
                    use_container_width=True,
                    type="primary" if is_page_selected else "secondary",
                ):
                    st.session_state.nav_module = module_name
                    st.session_state.nav_page = page_name
                    # 只展开当前模块，不关闭其他已展开的模块
                    st.session_state[expander_key] = True
                    st.rerun()

    st.sidebar.markdown('<hr class="nav-divider">', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="sidebar-footer">Produced by wyy 😜</div>',
        unsafe_allow_html=True,
    )

    return st.session_state.nav_module, st.session_state.nav_page


def dispatch_page(module_name: str, page_name: str):
    """根据导航配置动态加载并运行对应子页面。"""
    if module_name == "数据处理":
        import modules.module1.mod1_etl as mod1_etl
        mod1_etl.run(page_name=page_name)
    else:
        module_path = NAV_CONFIG[module_name]["pages"][page_name]
        mod = importlib.import_module(module_path)
        mod.run()

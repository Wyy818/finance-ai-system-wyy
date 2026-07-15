import streamlit as st
from utils.navigation import dispatch_page, render_sidebar

st.set_page_config(page_title="业财融合多功能系统", layout="wide", initial_sidebar_state="expanded", menu_items={
    "Get Help": "https://example.com/help",
    "Report a bug": "https://example.com/bug",
    "About": "业财融合多功能系统 - 基于AI的数据处理平台"
})

st.markdown("""
<style>
    div[data-testid="stFileUploader"] label {
        font-size: 0.9rem;
        color: #333333;
    }
    div[data-testid="stFileUploader"] [data-testid="stDropzone"] {
        border: 2px dashed #cccccc;
        border-radius: 8px;
    }
    div[data-testid="stFileUploader"] [data-testid="stDropzone"]:hover {
        border-color: #87CEEB;
    }
    div[data-testid="stFileUploader"] [data-testid="stDropzone"] div {
        color: #666666;
    }
</style>
""", unsafe_allow_html=True)

module_name, page_name = render_sidebar()
dispatch_page(module_name, page_name)

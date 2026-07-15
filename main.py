import streamlit as st
from utils.navigation import dispatch_page, render_sidebar

st.set_page_config(page_title="业财数据平台", layout="wide", initial_sidebar_state="expanded")

module_name, page_name = render_sidebar()
dispatch_page(module_name, page_name)

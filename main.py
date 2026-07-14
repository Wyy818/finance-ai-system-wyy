import streamlit as st
from modules.mod1_etl import run as run_etl
from modules.mod2_analysis import run as run_analysis
from modules.mod3_visualization import run as run_viz

st.set_page_config(page_title="业财数据平台", layout="wide")

# 侧边栏导航
st.sidebar.title("🚀 业财数据平台")
module = st.sidebar.radio(
    "选择功能模块",
    ["数据处理", "AI 异常分析", "数据可视化"]
)

# 路由分发
if module == "数据处理":
    run_etl()
elif module == "AI 异常分析":
    run_analysis()
elif module == "数据可视化":
    run_viz()
import streamlit as st
import pandas as pd
from utils.db_manager import save_to_db

def run():
    st.title("🧠 模块二：AI 异常分析")
    
    # 独立上传（即使模块1传过了，这里也可以传新文件）
    uploaded_file = st.file_uploader("上传待分析报表", type=["xlsx", "csv"], key="ai_upload")
    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 独立存库
        save_to_db(df, f"analysis_{uploaded_file.name.split('.')[0]}")
        
        st.text_area("输入分析指令", "请分析以下数据的异常指标")
        if st.button("🤖 开始分析"):
            st.write("AI 正在分析... (此处接入 Ollama)")
            
    # 独立导出
    st.divider()
    if st.button("📥 导出分析报告"):
        st.info("（此处接入报告导出逻辑）")
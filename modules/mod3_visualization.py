import streamlit as st
import pandas as pd
from utils.db_manager import save_to_db

def run():
    st.title("📊 模块三：数据可视化")
    
    # 独立上传
    uploaded_file = st.file_uploader("上传绘图数据", type=["xlsx", "csv"], key="viz_upload")
    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        save_to_db(df, f"viz_{uploaded_file.name.split('.')[0]}")
        
        col1, col2 = st.columns(2)
        with col1: x_col = st.selectbox("X轴", df.columns)
        with col2: y_col = st.selectbox("Y轴", df.columns)
        
        if st.button("🎨 生成图表"):
            st.bar_chart(df, x=x_col, y=y_col)
            
    # 独立导出
    st.divider()
    if st.button("📥 导出图表为图片"):
        st.info("（此处接入图表导出逻辑）")
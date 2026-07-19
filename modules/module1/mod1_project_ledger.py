import io

import pandas as pd
import streamlit as st

from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state, render_sheet_selector

PREFIX = "mod1_project"


def run():
    st.title("📋 业务台账处理")
    st.caption("处理工程项目和政企项目台账数据")

    init_module_state(PREFIX, {})

    df_key = f"{PREFIX}_df"
    all_key = f"{PREFIX}_all_dfs"

    uploaded_df = handle_file_upload(PREFIX, "上传业务台账")
    
    all_dfs = st.session_state.get(all_key, {})
    
    st.subheader("选择处理对象")
    uploaded_df = render_sheet_selector(PREFIX, all_dfs)

    if uploaded_df is not None:
        st.success(f"当前数据：{len(uploaded_df)} 行 × {len(uploaded_df.columns)} 列")
        with st.expander("数据预览", expanded=False):
            st.dataframe(uploaded_df.head(10), use_container_width=True)

        st.subheader("台账处理")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            date_col = st.selectbox("日期字段", options=[""] + list(uploaded_df.columns), key=f"{PREFIX}_date_col")
        with col2:
            amount_col = st.selectbox("金额字段", options=[""] + list(uploaded_df.columns), key=f"{PREFIX}_amount_col")
        with col3:
            project_col = st.selectbox("项目名称字段", options=[""] + list(uploaded_df.columns), key=f"{PREFIX}_project_col")

        if st.button("统计分析", key=f"{PREFIX}_analyze"):
            if project_col and amount_col:
                summary = uploaded_df.groupby(project_col)[amount_col].sum().reset_index()
                summary.columns = ["项目名称", "总金额"]
                st.subheader("项目金额汇总")
                st.dataframe(summary, use_container_width=True)

                total_amount = uploaded_df[amount_col].sum()
                project_count = uploaded_df[project_col].nunique()
                avg_amount = total_amount / project_count if project_count > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("项目总数", project_count)
                with col2:
                    st.metric("总金额", f"{total_amount:,.2f}")
                with col3:
                    st.metric("平均金额", f"{avg_amount:,.2f}")

        if st.button("存入数据库", key=f"{PREFIX}_save_db"):
            save_to_db(uploaded_df, "project_ledger")
            st.success("数据已安全入库！")

        output = io.BytesIO()
        uploaded_df.to_excel(output, index=False)
        st.download_button(
            label="导出为 Excel",
            data=output.getvalue(),
            file_name="project_ledger.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{PREFIX}_export",
        )
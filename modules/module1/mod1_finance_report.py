import io

import pandas as pd
import streamlit as st

from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state, render_sheet_selector

PREFIX = "mod1_finance"


def run():
    st.title("📊 财务报表处理")
    st.caption("处理财务报表数据，支持资产负债表、利润表、现金流量表")

    init_module_state(PREFIX, {})

    df_key = f"{PREFIX}_df"
    all_key = f"{PREFIX}_all_dfs"

    uploaded_df = handle_file_upload(PREFIX, "上传财务报表")
    
    all_dfs = st.session_state.get(all_key, {})
    
    st.subheader("选择处理对象")
    uploaded_df = render_sheet_selector(PREFIX, all_dfs)

    if uploaded_df is not None:
        st.success(f"当前数据：{len(uploaded_df)} 行 × {len(uploaded_df.columns)} 列")
        with st.expander("数据预览", expanded=False):
            st.dataframe(uploaded_df.head(10), use_container_width=True)

        st.subheader("报表类型识别")
        report_type = st.selectbox("选择报表类型", ["自动识别", "资产负债表", "利润表", "现金流量表"], key=f"{PREFIX}_report_type")

        if report_type == "利润表" or (report_type == "自动识别" and any("收入" in col for col in uploaded_df.columns)):
            st.subheader("利润表分析")
            
            col1, col2 = st.columns(2)
            with col1:
                revenue_col = st.selectbox("营业收入字段", options=[""] + list(uploaded_df.columns), key=f"{PREFIX}_revenue_col")
            with col2:
                profit_col = st.selectbox("净利润字段", options=[""] + list(uploaded_df.columns), key=f"{PREFIX}_profit_col")

            if st.button("计算指标", key=f"{PREFIX}_calc"):
                if revenue_col and profit_col:
                    total_revenue = uploaded_df[revenue_col].sum()
                    total_profit = uploaded_df[profit_col].sum()
                    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("营业收入", f"{total_revenue:,.2f}")
                    with col2:
                        st.metric("净利润", f"{total_profit:,.2f}")
                    with col3:
                        st.metric("净利润率", f"{profit_margin:.2f}%")

        if st.button("存入数据库", key=f"{PREFIX}_save_db"):
            save_to_db(uploaded_df, "finance_report")
            st.success("数据已安全入库！")

        output = io.BytesIO()
        uploaded_df.to_excel(output, index=False)
        st.download_button(
            label="导出为 Excel",
            data=output.getvalue(),
            file_name="finance_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{PREFIX}_export",
        )
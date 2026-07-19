import io

import pandas as pd
import streamlit as st

from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state, render_sheet_selector

PREFIX = "module4"


def run():
    st.title("📝 数据分析报告")
    st.caption("上传模板表，自动填充数据并导出报告")

    init_module_state(PREFIX, {"template_df": None, "data_df": None})

    template_key = f"{PREFIX}_template_df"
    data_key = f"{PREFIX}_data_df"

    st.subheader("📋 上传模板")
    template_files = st.file_uploader(
        "上传报告模板（Excel格式）",
        type=["xlsx"],
        key=f"{PREFIX}_template_upload",
        accept_multiple_files=False,
        help="支持 Excel (.xlsx) 格式的模板文件"
    )

    if template_files:
        template_df = pd.read_excel(template_files)
        st.session_state[template_key] = template_df
        st.success("模板上传成功！")
        with st.expander("模板预览", expanded=False):
            st.dataframe(template_df, use_container_width=True)

    st.subheader("📊 上传数据")
    data_df = handle_file_upload(PREFIX, "上传数据源")
    
    all_dfs = st.session_state.get(f"{PREFIX}_all_dfs", {})
    
    st.subheader("选择处理对象")
    data_df = render_sheet_selector(PREFIX, all_dfs)

    if data_df is not None:
        st.success(f"当前数据：{len(data_df)} 行 × {len(data_df.columns)} 列")
        with st.expander("数据预览", expanded=False):
            st.dataframe(data_df.head(10), use_container_width=True)

    template_df = st.session_state.get(template_key)
    if template_df is not None and data_df is not None:
        st.subheader("🔄 数据映射")
        
        col1, col2 = st.columns(2)
        template_cols = list(template_df.columns)
        data_cols = list(data_df.columns)

        mappings = {}
        for col in template_cols:
            with col1:
                st.markdown(f"**{col}**")
            with col2:
                mappings[col] = st.selectbox(
                    f"映射到 {col}",
                    options=[""] + data_cols,
                    key=f"{PREFIX}_mapping_{col}"
                )

        if st.button("生成报告", key=f"{PREFIX}_generate", type="primary"):
            with st.spinner("正在填充报告..."):
                result_df = template_df.copy()
                
                for template_col, data_col in mappings.items():
                    if data_col and data_col in data_df.columns:
                        data_values = data_df[data_col].tolist()
                        for i, val in enumerate(data_values):
                            if i < len(result_df):
                                result_df.loc[i, template_col] = val

                st.subheader("📄 报告预览")
                st.dataframe(result_df, use_container_width=True)

                st.session_state[f"{PREFIX}_result_df"] = result_df

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    result_df.to_excel(writer, index=False, sheet_name='报告')
                output.seek(0)
                
                st.download_button(
                    label="导出报告（Excel）",
                    data=output.getvalue(),
                    file_name="analysis_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"{PREFIX}_export",
                )

    st.divider()
    st.info("💡 提示：上传模板后，通过字段映射将数据源中的数据自动填充到模板对应位置")
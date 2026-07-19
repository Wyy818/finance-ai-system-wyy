import io
from typing import List, Optional

import pandas as pd
import streamlit as st

from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state, render_sheet_selector

PREFIX = "module1"
INVALID_PLACEHOLDERS = ["#N/A", "N/A", "n/a", "null", "NULL", "None", "none", "-", "--", "NaN", "nan"]


def _render_file_ops_checkboxes() -> dict:
    st.subheader("📋 表格处理选项")
    col1, col2, col3 = st.columns(3)
    with col1:
        merge = st.checkbox("合并", key=f"{PREFIX}_op_merge", help="勾选后可将多个上传文件纵向拼接")
        clean_blank = st.checkbox("清洗空白值", key=f"{PREFIX}_op_clean_blank", help="去除空行及纯空白单元格")
    with col2:
        clean_invalid = st.checkbox("清洗无效值", key=f"{PREFIX}_op_clean_invalid", help="将 #N/A、null 等无效占位符视为空值")
        deduplicate = st.checkbox("去重", key=f"{PREFIX}_op_deduplicate", help="删除完全重复的行")
    with col3:
        strip_whitespace = st.checkbox("去除首尾空格", key=f"{PREFIX}_op_strip", help="清理文本列首尾空白字符")

    return {
        "merge": merge,
        "clean_blank": clean_blank,
        "clean_invalid": clean_invalid,
        "deduplicate": deduplicate,
        "strip_whitespace": strip_whitespace,
    }


def _apply_file_operations(
    df: pd.DataFrame, ops: dict, extra_dfs: Optional[List[pd.DataFrame]] = None
) -> pd.DataFrame:
    result = df.copy()

    if ops.get("merge") and extra_dfs:
        result = pd.concat([result, *extra_dfs], ignore_index=True)

    if ops.get("strip_whitespace"):
        for col in result.select_dtypes(include=["object", "string"]).columns:
            result[col] = result[col].astype(str).str.strip()

    if ops.get("clean_blank"):
        result = result.replace(r"^\s*$", pd.NA, regex=True)
        result = result.dropna(how="all")

    if ops.get("clean_invalid"):
        result = result.replace(INVALID_PLACEHOLDERS, pd.NA)
        result = result.dropna(how="all")

    if ops.get("deduplicate"):
        result = result.drop_duplicates()

    return result


def _apply_selected_operations(ops: dict) -> Optional[pd.DataFrame]:
    df_key = f"{PREFIX}_df"
    extra_key = f"{PREFIX}_extra_dfs"
    df = st.session_state.get(df_key)
    if df is None:
        return None

    extra_dfs = st.session_state.get(extra_key, []) if ops.get("merge") else None
    if ops.get("merge") and not extra_dfs:
        st.warning("已勾选「合并」，请上传至少 2 个文件。")
        return df

    result = _apply_file_operations(df, ops, extra_dfs)
    st.session_state[df_key] = result
    if ops.get("merge"):
        st.session_state[extra_key] = []
    return result


def run():
    st.title("📋 常规表格处理")
    st.caption("勾选处理选项后一键应用，与「AI 智能清洗」共享同一份数据")
    
    init_module_state(PREFIX)
    
    df_key = f"{PREFIX}_df"
    all_key = f"{PREFIX}_all_dfs"
    sel_key = f"{PREFIX}_selected_sheets"
    
    uploaded_df = handle_file_upload(PREFIX, "上传原始报表")
    
    all_dfs = st.session_state.get(all_key, {})
    
    st.subheader("📋 选择处理对象")
    uploaded_df = render_sheet_selector(PREFIX, all_dfs)
    
    if uploaded_df is not None:
        st.success(f"当前数据：{len(uploaded_df)} 行 × {len(uploaded_df.columns)} 列")
        with st.expander("数据预览", expanded=False):
            st.dataframe(uploaded_df.head(10), use_container_width=True)
    
    st.divider()
    
    if uploaded_df is not None:
        st.session_state[df_key] = uploaded_df
        st.session_state[all_key] = {"当前数据": uploaded_df}
        st.session_state[sel_key] = ["当前数据"]
    
    ops = _render_file_ops_checkboxes()

    col_apply, col_info = st.columns([1, 3])
    with col_apply:
        if st.button("⚙️ 应用所选操作", key=f"{PREFIX}_proc_apply_ops", type="primary"):
            if st.session_state.get(df_key) is None:
                st.warning("请先上传表格文件！")
            else:
                before = len(st.session_state[df_key])
                _apply_selected_operations(ops)
                after = len(st.session_state[df_key])
                st.success(f"操作完成：{before} 行 → {after} 行")

    with col_info:
        if st.session_state.get(df_key) is not None:
            st.info("提示：处理结果会同步到模块一的其他子页面。")

    all_dfs = st.session_state.get(all_key, {})
    sel_sheets = st.session_state.get(sel_key, [])
    if all_dfs and len(all_dfs) > 1:
        st.subheader("📋 选择数据源")
        options = list(all_dfs.keys())
        selected = st.multiselect(
            "选择要处理的 Sheet（可多选）",
            options=options,
            default=sel_sheets if sel_sheets else [options[0]],
            key=f"{PREFIX}_proc_sheet_selector",
            help="可选择不同文件或不同 Sheet"
        )
        if selected:
            st.session_state[sel_key] = selected
            st.session_state[df_key] = all_dfs[selected[0]]

    if st.session_state.get(df_key) is not None:
        st.subheader("处理结果预览")
        st.dataframe(st.session_state[df_key], use_container_width=True, height=400)
    
    if uploaded_df is not None:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 存入数据库", key=f"{PREFIX}_save_db"):
                save_to_db(st.session_state.get(df_key, uploaded_df), "processed_data")
                st.success("数据已安全入库！")
        with col2:
            output = io.BytesIO()
            st.session_state.get(df_key, uploaded_df).to_excel(output, index=False)
            st.download_button(
                label="📥 导出为 Excel",
                data=output.getvalue(),
                file_name="processed_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{PREFIX}_export",
            )
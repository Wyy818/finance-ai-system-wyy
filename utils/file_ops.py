from typing import List, Optional

import pandas as pd
import streamlit as st

INVALID_PLACEHOLDERS = ["#N/A", "N/A", "n/a", "null", "NULL", "None", "none", "-", "--", "NaN", "nan"]


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    return pd.read_csv(uploaded_file)


def render_file_ops_checkboxes(prefix: str) -> dict:
    """渲染文件处理复选框，选项保存在 session_state 中。"""
    st.subheader("📋 文件处理选项")
    col1, col2, col3 = st.columns(3)
    with col1:
        merge = st.checkbox("合并", key=f"{prefix}_op_merge", help="勾选后可将多个上传文件纵向拼接")
        clean_blank = st.checkbox("清洗空白值", key=f"{prefix}_op_clean_blank", help="去除空行及纯空白单元格")
    with col2:
        clean_invalid = st.checkbox("清洗无效值", key=f"{prefix}_op_clean_invalid", help="将 #N/A、null 等无效占位符视为空值")
        deduplicate = st.checkbox("去重", key=f"{prefix}_op_deduplicate", help="删除完全重复的行")
    with col3:
        strip_whitespace = st.checkbox("去除首尾空格", key=f"{prefix}_op_strip", help="清理文本列首尾空白字符")

    return {
        "merge": merge,
        "clean_blank": clean_blank,
        "clean_invalid": clean_invalid,
        "deduplicate": deduplicate,
        "strip_whitespace": strip_whitespace,
    }


def apply_file_operations(df: pd.DataFrame, ops: dict, extra_dfs: Optional[List[pd.DataFrame]] = None) -> pd.DataFrame:
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


def init_module_state(prefix: str, defaults: Optional[dict] = None):
    """初始化模块 session_state，切换页面时保留已有数据。"""
    base = {"df": None, "file_signature": None, "extra_dfs": []}
    if defaults:
        base.update(defaults)
    for name, value in base.items():
        key = f"{prefix}_{name}"
        if key not in st.session_state:
            st.session_state[key] = value


def handle_file_upload(prefix: str, label: str = "📂 上传文件") -> Optional[pd.DataFrame]:
    """
    上传文件并缓存到 session_state；仅在新文件时重新读取，切换模块不会丢失已处理数据。
    """
    df_key = f"{prefix}_df"
    sig_key = f"{prefix}_file_signature"
    extra_key = f"{prefix}_extra_dfs"

    merge_enabled = st.session_state.get(f"{prefix}_op_merge", False)
    uploaded_files = st.file_uploader(
        label,
        type=["xlsx", "csv"],
        key=f"{prefix}_upload",
        accept_multiple_files=merge_enabled,
    )

    if not uploaded_files:
        return st.session_state.get(df_key)

    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    signature = "|".join(f"{f.name}_{f.size}" for f in uploaded_files)
    if st.session_state.get(sig_key) != signature:
        dfs = [read_uploaded_file(f) for f in uploaded_files]
        st.session_state[df_key] = dfs[0]
        st.session_state[extra_key] = dfs[1:] if len(dfs) > 1 else []
        st.session_state[sig_key] = signature

    return st.session_state.get(df_key)


def apply_selected_operations(prefix: str, ops: dict) -> Optional[pd.DataFrame]:
    """根据复选框选项处理当前模块缓存的数据。"""
    df_key = f"{prefix}_df"
    extra_key = f"{prefix}_extra_dfs"
    df = st.session_state.get(df_key)
    if df is None:
        return None

    extra_dfs = st.session_state.get(extra_key, []) if ops.get("merge") else None
    if ops.get("merge") and not extra_dfs:
        st.warning("已勾选「合并」，请上传至少 2 个文件。")
        return df

    result = apply_file_operations(df, ops, extra_dfs)
    st.session_state[df_key] = result
    if ops.get("merge"):
        st.session_state[extra_key] = []
    return result

from typing import List, Optional

import pandas as pd
import streamlit as st


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    return pd.read_csv(uploaded_file)


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

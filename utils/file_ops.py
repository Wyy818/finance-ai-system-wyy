from typing import List, Optional, Dict, Tuple

import pandas as pd
import streamlit as st


@st.cache_data(max_entries=10, ttl=3600)
def _read_file_cached(file_bytes: bytes, file_name: str) -> Dict[str, pd.DataFrame]:
    """缓存读取文件内容，避免重复解析"""
    import io
    result = {}
    
    if file_name.endswith(".xlsx"):
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        for sheet_name in xls.sheet_names:
            key = f"{file_name}-{sheet_name}"
            result[key] = pd.read_excel(xls, sheet_name=sheet_name)
    elif file_name.endswith(".csv"):
        result[f"{file_name}-Sheet1"] = pd.read_csv(io.BytesIO(file_bytes))
    
    return result


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    return pd.read_csv(uploaded_file)


def read_uploaded_file_with_sheets(uploaded_file) -> Dict[str, pd.DataFrame]:
    """
    读取上传文件的所有sheet，返回字典 {"文件名-Sheet名": DataFrame}
    """
    file_bytes = uploaded_file.getvalue()
    return _read_file_cached(file_bytes, uploaded_file.name)


def init_module_state(prefix: str, defaults: Optional[dict] = None):
    """初始化模块 session_state，切换页面时保留已有数据。"""
    base = {"df": None, "file_signature": None, "extra_dfs": [], "all_dfs": {}, "selected_sheets": []}
    if defaults:
        base.update(defaults)
    for name, value in base.items():
        key = f"{prefix}_{name}"
        if key not in st.session_state:
            st.session_state[key] = value


def handle_file_upload(prefix: str, label: str = "上传文件") -> Optional[pd.DataFrame]:
    """
    上传文件并缓存到 session_state；支持多文件和多sheet。
    返回主DataFrame，同时在session_state中存储 all_dfs 字典。
    """
    df_key = f"{prefix}_df"
    sig_key = f"{prefix}_file_signature"
    all_key = f"{prefix}_all_dfs"
    sel_key = f"{prefix}_selected_sheets"

    uploaded_files = st.file_uploader(
        label,
        type=["xlsx", "csv"],
        key=f"{prefix}_upload",
        accept_multiple_files=True,
        help="支持 Excel (.xlsx) 和 CSV 文件格式，可同时上传多个文件",
    )

    if not uploaded_files:
        return st.session_state.get(df_key)

    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    signature = "|".join(f"{f.name}_{f.size}" for f in uploaded_files)
    if st.session_state.get(sig_key) != signature:
        all_dfs = {}
        for f in uploaded_files:
            sheets_dict = read_uploaded_file_with_sheets(f)
            all_dfs.update(sheets_dict)
        
        st.session_state[all_key] = all_dfs
        
        if all_dfs:
            first_key = next(iter(all_dfs.keys()))
            st.session_state[df_key] = all_dfs[first_key]
            st.session_state[sel_key] = [first_key]
        
        st.session_state[sig_key] = signature

    return st.session_state.get(df_key)


def render_sheet_selector(prefix: str, all_dfs: Optional[dict] = None) -> Optional[pd.DataFrame]:
    """
    渲染选择处理对象下拉框，支持选择文件名和sheet名
    返回选中的DataFrame
    """
    df_key = f"{prefix}_df"
    sel_key = f"{prefix}_selected_sheets"
    
    if all_dfs is None:
        all_dfs = st.session_state.get(f"{prefix}_all_dfs", {})
    
    if not all_dfs:
        return st.session_state.get(df_key)
    
    options = list(all_dfs.keys())
    current_selected = st.session_state.get(sel_key, [options[0]] if options else [])
    
    selected = st.multiselect(
        "选择处理对象",
        options=options,
        default=current_selected,
        key=f"{prefix}_sheet_selector",
        help="可多选，选择多个将激活跨表操作"
    )
    
    st.session_state[sel_key] = selected
    
    if selected:
        st.session_state[df_key] = all_dfs[selected[0]]
        return all_dfs[selected[0]]
    
    return st.session_state.get(df_key)

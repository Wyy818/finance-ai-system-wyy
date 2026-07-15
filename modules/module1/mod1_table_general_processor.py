import io
from typing import List, Optional

import pandas as pd
import streamlit as st

from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state

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


def run(df=None):
    init_module_state(PREFIX)
    
    df_key = f"{PREFIX}_df"
    if df is not None:
        st.session_state[df_key] = df
    
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
            st.info("提示：处理结果会同步到模块一的「AI 智能清洗」子页面。")

    if st.session_state.get(df_key) is not None:
        st.subheader("处理结果预览")
        st.dataframe(st.session_state[df_key], use_container_width=True, height=400)


def _init_custom_state(prefix: str):
    default_values = {
        f"{prefix}_filter_row_count": 1,
        f"{prefix}_filter_rows": [{}],
        f"{prefix}_op_row_count": 1,
        f"{prefix}_op_rows": [],
        f"{prefix}_formula_selected": "",
        f"{prefix}_formula_params": {},
        f"{prefix}_pivot_rows": [],
        f"{prefix}_pivot_cols": [],
        f"{prefix}_pivot_values": [],
        f"{prefix}_pivot_value_count": 0,
        f"{prefix}_cross_op_type": "",
        f"{prefix}_current_df": pd.DataFrame(),
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    row_count = st.session_state[f"{prefix}_filter_row_count"]
    for i in range(row_count):
        if f"{prefix}_filter_field_{i}" not in st.session_state:
            st.session_state[f"{prefix}_filter_field_{i}"] = ""
        if f"{prefix}_filter_values_{i}" not in st.session_state:
            st.session_state[f"{prefix}_filter_values_{i}"] = []
    
    op_count = st.session_state[f"{prefix}_op_row_count"]
    for i in range(op_count):
        if f"{prefix}_op_type_{i}" not in st.session_state:
            st.session_state[f"{prefix}_op_type_{i}"] = ""
        if f"{prefix}_op_fields_{i}" not in st.session_state:
            st.session_state[f"{prefix}_op_fields_{i}"] = []

    pivot_value_count = st.session_state[f"{prefix}_pivot_value_count"]
    for i in range(pivot_value_count):
        if f"{prefix}_pivot_value_field_{i}" not in st.session_state:
            st.session_state[f"{prefix}_pivot_value_field_{i}"] = ""
        if f"{prefix}_pivot_value_agg_{i}" not in st.session_state:
            st.session_state[f"{prefix}_pivot_value_agg_{i}"] = "求和"
    
    for i in range(5):
        if f"{prefix}_formula_param_{i}" not in st.session_state:
            st.session_state[f"{prefix}_formula_param_{i}"] = ""


def _render_sheet_selector(all_dfs: dict, prefix: str) -> list:
    if not all_dfs:
        return []
    options = list(all_dfs.keys())
    selected = st.multiselect(
        "选择处理对象",
        options=options,
        default=[options[0]],
        key=f"{prefix}_sheet_selected",
        help="可多选，选择多个将激活跨表操作"
    )
    return selected


def _render_dynamic_filter(columns: list, prefix: str) -> list:
    st.subheader("🔍 动态筛选")
    row_count = st.session_state[f"{prefix}_filter_row_count"]
    current_df = st.session_state.get(f"{prefix}_current_df", pd.DataFrame())
    
    for i in range(row_count):
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            field = st.selectbox(
                f"筛选字段 {i+1}",
                options=[""] + columns,
                key=f"{prefix}_filter_field_{i}",
                index=0
            )
        with col2:
            if field and not current_df.empty and field in current_df.columns:
                unique_vals = sorted(list(set(current_df[field].dropna().astype(str).tolist())))
                st.multiselect(
                    f"筛选值 {i+1}",
                    options=[""] + unique_vals,
                    key=f"{prefix}_filter_values_{i}"
                )
            else:
                st.multiselect(f"筛选值 {i+1}", options=[""], key=f"{prefix}_filter_values_{i}", disabled=True)
        with col3:
            if i > 0 and st.button("🗑️", key=f"{prefix}_filter_remove_{i}"):
                st.session_state[f"{prefix}_filter_row_count"] -= 1
                st.rerun()
    
    if st.button("➕ 添加筛选条件", key=f"{prefix}_filter_add"):
        st.session_state[f"{prefix}_filter_row_count"] += 1
        st.session_state[f"{prefix}_filter_rows"].append({})
        st.rerun()
    
    filters = []
    for i in range(row_count):
        field = st.session_state.get(f"{prefix}_filter_field_{i}")
        values = st.session_state.get(f"{prefix}_filter_values_{i}", [])
        if field and values:
            filters.append({"field": field, "values": values})
    return filters


def _apply_dynamic_filter(df: pd.DataFrame, filters: list) -> pd.DataFrame:
    if not filters:
        return df
    result = df.copy()
    for f in filters:
        result = result[result[f["field"]].astype(str).isin(f["values"])]
    return result


def _render_post_filter_ops(columns: list, prefix: str) -> list:
    st.subheader("⚙️ 筛选后操作")
    op_types = [
        "求和", "求平均", "计数",
        "升序", "降序",
        "删除重复值", "删除筛选行", "保留筛选行",
        "拼接-"
    ]
    row_count = st.session_state[f"{prefix}_op_row_count"]
    
    for i in range(row_count):
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            op_type = st.selectbox(
                f"操作类型 {i+1}",
                options=[""] + op_types,
                key=f"{prefix}_op_type_{i}",
                index=0
            )
        with col2:
            if op_type and op_type not in ["删除重复值", "删除筛选行", "保留筛选行"]:
                st.multiselect(
                    f"操作字段 {i+1}",
                    options=[""] + columns,
                    key=f"{prefix}_op_fields_{i}"
                )
            else:
                st.multiselect(f"操作字段 {i+1}", options=[""], key=f"{prefix}_op_fields_{i}", disabled=True)
        with col3:
            if st.button("🗑️", key=f"{prefix}_op_remove_{i}"):
                st.session_state[f"{prefix}_op_row_count"] -= 1
                st.rerun()
    
    if st.button("➕ 添加操作", key=f"{prefix}_op_add"):
        st.session_state[f"{prefix}_op_row_count"] += 1
        st.session_state[f"{prefix}_op_rows"].append({})
        st.rerun()
    
    ops = []
    for i in range(row_count):
        op_type = st.session_state.get(f"{prefix}_op_type_{i}")
        fields = st.session_state.get(f"{prefix}_op_fields_{i}", [])
        if op_type:
            ops.append({"op_type": op_type, "fields": fields})
    return ops


def _apply_post_filter_ops(df: pd.DataFrame, ops: list) -> pd.DataFrame:
    if not ops:
        return df
    result = df.copy()
    for op in ops:
        op_type = op["op_type"]
        fields = op["fields"]
        
        if op_type == "求和":
            for field in fields:
                if field in result.columns:
                    result[f"求和-{field}"] = result[field].sum()
        elif op_type == "求平均":
            for field in fields:
                if field in result.columns:
                    result[f"平均-{field}"] = result[field].mean()
        elif op_type == "计数":
            for field in fields:
                if field in result.columns:
                    result[f"计数-{field}"] = result[field].count()
        elif op_type == "升序":
            if fields:
                result = result.sort_values(by=fields, ascending=True)
        elif op_type == "降序":
            if fields:
                result = result.sort_values(by=fields, ascending=False)
        elif op_type == "删除重复值":
            result = result.drop_duplicates()
        elif op_type == "删除筛选行":
            result = result.dropna(how="all")
        elif op_type == "保留筛选行":
            result = result.dropna(how="any")
        elif op_type == "拼接-":
            if len(fields) >= 2:
                new_col = "-".join(fields)
                result[new_col] = result[fields].astype(str).agg("-".join, axis=1)
    
    return result


FORMULA_INFO = {
    "SUMIFS": {
        "syntax": "SUMIFS(求和区域, 条件区域1, 条件1, [条件区域2, 条件2], ...)",
        "desc": "对满足多个条件的单元格求和",
        "params": ["求和区域", "条件区域1", "条件1", "条件区域2", "条件2"]
    },
    "AVERAGE": {
        "syntax": "AVERAGE(数值1, [数值2], ...)",
        "desc": "计算平均值",
        "params": ["数值区域"]
    },
    "XLOOKUP": {
        "syntax": "XLOOKUP(查找值, 查找区域, 返回区域, [未找到值], [匹配模式], [搜索模式])",
        "desc": "在区域中查找值并返回对应结果",
        "params": ["查找值", "查找区域", "返回区域", "匹配模式"]
    },
    "FILTER": {
        "syntax": "FILTER(数组, 包含条件的数组, [如果为空则返回的值])",
        "desc": "根据条件筛选数组",
        "params": ["筛选区域", "条件区域"]
    },
    "TEXTJOIN": {
        "syntax": "TEXTJOIN(分隔符, 忽略空单元格, 文本1, [文本2], ...)",
        "desc": "使用分隔符连接多个字段的文本",
        "params": ["分隔符", "忽略空值", "文本区域1", "文本区域2"]
    }
}


def _render_formula_simulator(columns: list, prefix: str, all_dfs: dict = None) -> dict:
    st.subheader("📐 Excel 公式模拟")
    formulas = sorted(list(FORMULA_INFO.keys()))
    selected = st.selectbox(
        "选择公式",
        options=[""] + formulas,
        key=f"{prefix}_formula_selected",
        index=0
    )
    
    if selected:
        info = FORMULA_INFO[selected]
        st.markdown(f"**语法**: `{info['syntax']}`")
        st.markdown(f"**说明**: {info['desc']}")
        
        all_columns = columns
        if all_dfs and len(all_dfs) > 1:
            for sheet_name, df_sheet in all_dfs.items():
                for col in df_sheet.columns:
                    all_columns.append(f"{sheet_name}-{col}")
        
        params = {}
        for i, param_name in enumerate(info["params"]):
            if param_name in ["查找值", "条件1", "条件2", "分隔符"]:
                params[param_name] = st.text_input(
                    f"{param_name}",
                    key=f"{prefix}_formula_param_{i}",
                    placeholder="输入值或列名"
                )
            elif param_name == "匹配模式":
                params[param_name] = st.selectbox(
                    param_name,
                    options=["0 (精确匹配)", "1 (近似<=)", "-1 (近似>=)", "2 (通配符)"],
                    key=f"{prefix}_formula_param_{i}"
                )
            elif param_name == "忽略空值":
                params[param_name] = st.checkbox(param_name, key=f"{prefix}_formula_param_{i}")
            elif selected == "XLOOKUP" and param_name in ["查找区域", "返回区域"]:
                params[param_name] = st.selectbox(
                    param_name,
                    options=[""] + all_columns,
                    key=f"{prefix}_formula_param_{i}",
                    index=0
                )
            else:
                params[param_name] = st.selectbox(
                    param_name,
                    options=[""] + columns,
                    key=f"{prefix}_formula_param_{i}",
                    index=0
                )
        
        st.session_state[f"{prefix}_formula_params"] = params
        return {"formula": selected, "params": params}
    return {}


def _apply_formula(df: pd.DataFrame, formula_config: dict, all_dfs: dict = None) -> pd.DataFrame:
    if not formula_config:
        return df
    result = df.copy()
    formula = formula_config["formula"]
    params = formula_config["params"]
    
    if all_dfs is None:
        all_dfs = {"当前数据": df}
    
    if formula == "SUMIFS":
        sum_col = params.get("求和区域")
        cond_col1 = params.get("条件区域1")
        cond_val1 = params.get("条件1")
        
        if sum_col and cond_col1 and sum_col in result.columns and cond_col1 in result.columns:
            if cond_val1:
                mask = result[cond_col1].astype(str) == str(cond_val1)
                sum_result = result.loc[mask, sum_col].sum()
                result[f"SUMIFS-{sum_col}"] = sum_result
            else:
                result[f"SUMIFS-{sum_col}"] = result.groupby(cond_col1)[sum_col].transform('sum')
    
    elif formula == "AVERAGE":
        col = params.get("数值区域")
        if col in result.columns:
            result[f"AVERAGE-{col}"] = result[col].mean()
    
    elif formula == "XLOOKUP":
        lookup_col = params.get("查找区域")
        return_col = params.get("返回区域")
        match_mode = params.get("匹配模式", "0 (精确匹配)")
        
        if not lookup_col or not return_col:
            return result
        
        lookup_sheet = "当前数据"
        return_sheet = "当前数据"
        lookup_col_name = lookup_col
        return_col_name = return_col
        
        if "-" in lookup_col:
            parts = lookup_col.split("-", 1)
            lookup_sheet = parts[0]
            lookup_col_name = parts[1]
        
        if "-" in return_col:
            parts = return_col.split("-", 1)
            return_sheet = parts[0]
            return_col_name = parts[1]
        
        lookup_df = all_dfs.get(lookup_sheet, result)
        return_df = all_dfs.get(return_sheet, result)
        
        if lookup_col_name not in lookup_df.columns or return_col_name not in return_df.columns:
            return result
        
        mode = int(match_mode.split()[0])
        lookup_series = result[lookup_col_name] if lookup_sheet == "当前数据" else result[lookup_col_name]
        
        if mode == 0:
            lookup_map = lookup_df.set_index(lookup_col_name)[return_col_name].drop_duplicates()
            result[f"XLOOKUP-{lookup_col}"] = lookup_series.map(lookup_map)
        elif mode == 1:
            lookup_df_sorted = lookup_df[[lookup_col_name, return_col_name]].sort_values(lookup_col_name).drop_duplicates(subset=[lookup_col_name], keep='last')
            result_sorted = result.sort_values(lookup_col_name)
            merged = pd.merge_asof(result_sorted, lookup_df_sorted, left_on=lookup_col_name, right_on=lookup_col_name, direction='backward')
            result[f"XLOOKUP-{lookup_col}"] = merged[return_col_name + '_y'].reindex(result.index)
        elif mode == -1:
            lookup_df_sorted = lookup_df[[lookup_col_name, return_col_name]].sort_values(lookup_col_name).drop_duplicates(subset=[lookup_col_name], keep='first')
            result_sorted = result.sort_values(lookup_col_name)
            merged = pd.merge_asof(result_sorted, lookup_df_sorted, left_on=lookup_col_name, right_on=lookup_col_name, direction='forward')
            result[f"XLOOKUP-{lookup_col}"] = merged[return_col_name + '_y'].reindex(result.index)
    
    elif formula == "FILTER":
        filter_col = params.get("筛选区域")
        cond_col = params.get("条件区域")
        if filter_col and cond_col:
            result = result[result[cond_col].notna()]
    
    elif formula == "TEXTJOIN":
        delimiter = params.get("分隔符", ",")
        ignore_empty = params.get("忽略空值", True)
        text_col1 = params.get("文本区域1")
        text_col2 = params.get("文本区域2")
        
        text_cols = [c for c in [text_col1, text_col2] if c and c in result.columns]
        if len(text_cols) >= 2:
            result[f"TEXTJOIN-{'-'.join(text_cols)}"] = result[text_cols].astype(str).agg(delimiter.join, axis=1)
    
    return result


def _render_pivot_table(columns: list, prefix: str) -> dict:
    st.subheader("📊 数据透视表")

    st.markdown("**行标题**")
    rows = st.multiselect("选择行字段", options=columns, key=f"{prefix}_pivot_rows")

    st.markdown("**列标题**")
    cols = st.multiselect("选择列字段", options=columns, key=f"{prefix}_pivot_cols")

    st.markdown("**值字段**")
    value_count = st.session_state.get(f"{prefix}_pivot_value_count", 0)
    for i in range(value_count):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.selectbox(f"值字段 {i+1}", [""] + columns, key=f"{prefix}_pivot_value_field_{i}")
        with col2:
            st.selectbox(f"聚合方式 {i+1}", ["求和", "计数", "平均", "最大值", "最小值"], key=f"{prefix}_pivot_value_agg_{i}")
        with col3:
            if i > 0 and st.button("🗑️", key=f"{prefix}_pivot_value_remove_{i}"):
                st.session_state[f"{prefix}_pivot_value_count"] -= 1
                st.rerun()
    if st.button("➕ 添加值字段", key=f"{prefix}_pivot_value_add"):
        st.session_state[f"{prefix}_pivot_value_count"] += 1
        st.rerun()

    pivot_values = []
    for i in range(value_count):
        field = st.session_state.get(f"{prefix}_pivot_value_field_{i}")
        agg = st.session_state.get(f"{prefix}_pivot_value_agg_{i}", "求和")
        if field:
            pivot_values.append({"field": field, "agg": agg})

    return {
        "rows": rows,
        "cols": cols,
        "values": pivot_values
    }


def _apply_pivot_table(df: pd.DataFrame, pivot_config: dict) -> pd.DataFrame:
    if not pivot_config["values"]:
        return df
    result = df.copy()

    agg_map = {"求和": "sum", "计数": "count", "平均": "mean", "最大值": "max", "最小值": "min"}
    values = {v["field"]: agg_map.get(v["agg"], "sum") for v in pivot_config["values"]}

    pivot = pd.pivot_table(
        result,
        index=pivot_config["rows"],
        columns=pivot_config["cols"],
        values=list(values.keys()),
        aggfunc=values,
        fill_value=0
    )
    return pivot


def _render_cross_sheet_ops(all_dfs: dict, prefix: str) -> dict:
    st.subheader("🔗 跨表/跨文件操作")
    op_types = ["纵向拼接 (pd.concat)", "横向连接 (pd.merge)", "跨表公式"]
    
    op_type = st.selectbox(
        "选择操作类型",
        options=[""] + op_types,
        key=f"{prefix}_cross_op_type",
        index=0
    )
    
    config = {"op_type": op_type}
    
    if op_type == "横向连接 (pd.merge)":
        left_key = st.selectbox("左表连接键", options=[""] + list(all_dfs.keys()), key=f"{prefix}_cross_left_key")
        right_key = st.selectbox("右表连接键", options=[""] + list(all_dfs.keys()), key=f"{prefix}_cross_right_key")
        
        left_cols = [""] + list(all_dfs[left_key].columns) if left_key else [""]
        right_cols = [""] + list(all_dfs[right_key].columns) if right_key else [""]
        
        left_col = st.selectbox("左表关联列", options=left_cols, key=f"{prefix}_cross_left_col")
        right_col = st.selectbox("右表关联列", options=right_cols, key=f"{prefix}_cross_right_col")
        how = st.selectbox("连接方式", ["left", "right", "inner", "outer"], key=f"{prefix}_cross_how")
        
        config.update({
            "left_key": left_key,
            "right_key": right_key,
            "left_col": left_col,
            "right_col": right_col,
            "how": how
        })
    
    return config


def _apply_cross_sheet_ops(all_dfs: dict, config: dict) -> pd.DataFrame:
    if not config["op_type"]:
        return list(all_dfs.values())[0] if all_dfs else pd.DataFrame()
    
    if config["op_type"] == "纵向拼接 (pd.concat)":
        return pd.concat(list(all_dfs.values()), ignore_index=True)
    
    elif config["op_type"] == "横向连接 (pd.merge)":
        left_df = all_dfs.get(config.get("left_key"))
        right_df = all_dfs.get(config.get("right_key"))
        if left_df is None or right_df is None:
            return pd.DataFrame()
        return pd.merge(
            left_df, right_df,
            left_on=config.get("left_col"),
            right_on=config.get("right_col"),
            how=config.get("how", "left")
        )
    
    return pd.DataFrame()


def render_custom_processing(df=None, uploaded_files=None):
    _init_custom_state(PREFIX)
    
    all_dfs = {}
    if df is not None:
        all_dfs["当前数据"] = df
    
    if uploaded_files:
        for file in uploaded_files:
            try:
                xls = pd.ExcelFile(file)
                for sheet_name in xls.sheet_names:
                    key = f"{file.name}-{sheet_name}"
                    all_dfs[key] = pd.read_excel(xls, sheet_name=sheet_name)
            except Exception as e:
                st.warning(f"读取文件 {file.name} 失败: {e}")
    
    if not all_dfs:
        st.info("请上传数据文件")
        return None
    
    selected_sheets = _render_sheet_selector(all_dfs, PREFIX)
    current_df = all_dfs[selected_sheets[0]] if selected_sheets else pd.DataFrame()
    st.session_state[f"{PREFIX}_current_df"] = current_df
    columns = list(current_df.columns)
    
    results = {}
    
    filters = _render_dynamic_filter(columns, PREFIX)
    if filters:
        try:
            filtered_df = _apply_dynamic_filter(current_df, filters)
            results["筛选结果"] = filtered_df
            st.dataframe(filtered_df.head(20), use_container_width=True, height=200)
        except Exception as e:
            st.warning(f"筛选操作执行失败: {e}")
            filtered_df = current_df
    else:
        filtered_df = current_df
    
    ops = _render_post_filter_ops(columns, PREFIX)
    if ops:
        try:
            processed_df = _apply_post_filter_ops(filtered_df, ops)
            results["操作结果"] = processed_df
            st.dataframe(processed_df.head(20), use_container_width=True, height=200)
        except Exception as e:
            st.warning(f"操作执行失败: {e}")
            processed_df = filtered_df
    else:
        processed_df = filtered_df
    
    formula_config = _render_formula_simulator(columns, PREFIX, all_dfs)
    if formula_config:
        try:
            formula_df = _apply_formula(processed_df, formula_config, all_dfs)
            results[f"公式-{formula_config['formula']}"] = formula_df
            st.dataframe(formula_df.head(20), use_container_width=True, height=200)
        except Exception as e:
            st.warning(f"公式计算失败: {e}")
            formula_df = processed_df
    else:
        formula_df = processed_df
    
    pivot_config = _render_pivot_table(columns, PREFIX)
    if pivot_config["values"]:
        try:
            pivot_result = _apply_pivot_table(formula_df, pivot_config)
            results["透视表"] = pivot_result
            st.dataframe(pivot_result.head(20), use_container_width=True, height=200)
        except Exception as e:
            st.warning(f"透视表生成失败: {e}")
            pivot_result = formula_df
    else:
        pivot_result = formula_df
    
    cross_sheet_enabled = len(selected_sheets) > 1
    cross_config = {}
    if cross_sheet_enabled:
        cross_config = _render_cross_sheet_ops({k: all_dfs[k] for k in selected_sheets}, PREFIX)
        if cross_config["op_type"]:
            try:
                cross_result = _apply_cross_sheet_ops({k: all_dfs[k] for k in selected_sheets}, cross_config)
                results[f"跨表-{cross_config['op_type']}"] = cross_result
                st.dataframe(cross_result.head(20), use_container_width=True, height=200)
            except Exception as e:
                st.warning(f"跨表操作失败: {e}")
    
    final_result = pivot_result
    if cross_sheet_enabled and cross_config.get("op_type"):
        final_result = results.get(f"跨表-{cross_config['op_type']}", pivot_result)
    
    st.session_state[f"{PREFIX}_custom_result"] = final_result
    
    return final_result

import streamlit as st

from utils.db_manager import save_to_db
from utils.file_ops import (
    apply_selected_operations,
    handle_file_upload,
    init_module_state,
    render_file_ops_checkboxes,
)

PREFIX = "viz"


def run():
    st.title("📊 模块三：数据可视化")

    init_module_state(PREFIX, {"x_col": None, "y_col": None, "chart_generated": False})

    df_key = f"{PREFIX}_df"
    x_key = f"{PREFIX}_x_col"
    y_key = f"{PREFIX}_y_col"
    chart_key = f"{PREFIX}_chart_generated"

    ops = render_file_ops_checkboxes(PREFIX)

    uploaded_df = handle_file_upload(PREFIX, "上传绘图数据")
    if uploaded_df is not None:
        st.success(f"当前数据：{len(st.session_state[df_key])} 行 × {len(st.session_state[df_key].columns)} 列")

    if st.button("⚙️ 应用所选操作", key=f"{PREFIX}_apply_ops"):
        if st.session_state.get(df_key) is None:
            st.warning("请先上传表格文件！")
        else:
            before = len(st.session_state[df_key])
            apply_selected_operations(PREFIX, ops)
            after = len(st.session_state[df_key])
            st.success(f"操作完成：{before} 行 → {after} 行")

    df = st.session_state.get(df_key)
    if df is not None:
        with st.expander("📊 当前数据预览", expanded=False):
            st.dataframe(df.head(10), use_container_width=True)

        save_to_db(df, "viz_data")

        columns = list(df.columns)
        default_x = st.session_state[x_key] if st.session_state[x_key] in columns else columns[0]
        default_y = (
            st.session_state[y_key]
            if st.session_state[y_key] in columns
            else (columns[1] if len(columns) > 1 else columns[0])
        )

        col1, col2 = st.columns(2)
        with col1:
            st.session_state[x_key] = st.selectbox("X轴", columns, index=columns.index(default_x), key=f"{PREFIX}_x")
        with col2:
            st.session_state[y_key] = st.selectbox("Y轴", columns, index=columns.index(default_y), key=f"{PREFIX}_y")

        if st.button("🎨 生成图表", key=f"{PREFIX}_chart"):
            st.session_state[chart_key] = True

        if st.session_state.get(chart_key):
            st.bar_chart(df, x=st.session_state[x_key], y=st.session_state[y_key])

    st.divider()
    if st.button("📥 导出图表为图片", key=f"{PREFIX}_export"):
        st.info("（此处接入图表导出逻辑）")

import streamlit as st

from utils.db_manager import get_all_tables, get_table_data, delete_table, save_to_db
from utils.file_ops import handle_file_upload, init_module_state, render_sheet_selector

PREFIX = "module6"


def run():
    st.title("🗄️ 数据库管理")
    st.caption("管理系统中的数据库表")

    init_module_state(PREFIX, {})

    tabs = st.tabs(["查看数据表", "导入数据", "数据查询"])

    with tabs[0]:
        st.subheader("数据表列表")
        tables = get_all_tables()
        
        if tables:
            selected_table = st.selectbox("选择数据表", tables, key=f"{PREFIX}_table_select")
            
            if selected_table:
                df = get_table_data(selected_table)
                st.success(f"表 {selected_table}：{len(df)} 行 × {len(df.columns)} 列")
                
                with st.expander("数据预览", expanded=False):
                    st.dataframe(df, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"删除表 {selected_table}", key=f"{PREFIX}_delete_table"):
                        delete_table(selected_table)
                        st.success(f"表 {selected_table} 已删除")
                        st.rerun()
        else:
            st.info("暂无数据表，请先导入数据")

    with tabs[1]:
        st.subheader("导入数据")
        uploaded_df = handle_file_upload(PREFIX, "上传数据")
        
        all_dfs = st.session_state.get(f"{PREFIX}_all_dfs", {})
        
        st.subheader("选择处理对象")
        uploaded_df = render_sheet_selector(PREFIX, all_dfs)

        if uploaded_df is not None:
            st.success(f"当前数据：{len(uploaded_df)} 行 × {len(uploaded_df.columns)} 列")
            with st.expander("数据预览", expanded=False):
                st.dataframe(uploaded_df.head(10), use_container_width=True)

            table_name = st.text_input("表名", value="new_table", key=f"{PREFIX}_new_table_name")
            
            if st.button("存入数据库", key=f"{PREFIX}_save_db", type="primary"):
                save_to_db(uploaded_df, table_name)
                st.success(f"数据已存入表 {table_name}！")

    with tabs[2]:
        st.subheader("数据查询")
        st.info("💡 提示：后续可扩展支持 SQL 查询功能")

    st.divider()
    st.info("💡 提示：数据库使用 SQLite，数据文件存储在本地")
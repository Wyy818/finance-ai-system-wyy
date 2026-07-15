import streamlit as st

from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state

PREFIX = "module2"


def run():
    st.title("🧠 AI 异常分析")
    st.caption("上传报表数据，由 AI 识别异常指标")

    init_module_state(PREFIX, {"prompt": "请分析以下数据的异常指标", "result": None})

    df_key = f"{PREFIX}_df"
    prompt_key = f"{PREFIX}_prompt"
    result_key = f"{PREFIX}_result"

    uploaded_df = handle_file_upload(PREFIX, "📂 上传待分析报表")
    if uploaded_df is not None:
        st.success(f"当前数据：{len(st.session_state[df_key])} 行 × {len(st.session_state[df_key].columns)} 列")

    if st.session_state.get(df_key) is not None:
        with st.expander("📊 数据预览", expanded=False):
            st.dataframe(st.session_state[df_key].head(10), use_container_width=True)

        st.session_state[prompt_key] = st.text_area(
            "输入分析指令",
            value=st.session_state[prompt_key],
            key=f"{PREFIX}_prompt_input",
        )

        if st.button("🤖 开始分析", key=f"{PREFIX}_run", type="primary"):
            save_to_db(st.session_state[df_key], "analysis_data")
            st.session_state[result_key] = "AI 正在分析... (此处接入 Ollama)"
            st.info(st.session_state[result_key])

        if st.session_state.get(result_key):
            st.write(st.session_state[result_key])

    st.divider()
    if st.button("📥 导出分析报告", key=f"{PREFIX}_export"):
        st.info("（此处接入报告导出逻辑）")

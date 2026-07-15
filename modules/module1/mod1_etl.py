import io
from typing import Optional

import pandas as pd
import streamlit as st

from utils.ai_service import get_ai_service
from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state, render_sheet_selector
from modules.module1 import mod1_table_general_processor

PREFIX = "module1"

PAGE_TITLES = {
    "AI 智能清洗": "🧹 AI 智能数据清洗",
    "常规表格处理": "📋 常规表格处理",
    "自定义处理": "🎛️ 自定义数据处理",
}

PAGE_CAPTIONS = {
    "AI 智能清洗": "通过自然语言对话，让 AI 生成并执行 Pandas 清洗代码",
    "常规表格处理": "勾选处理选项后一键应用，与「AI 智能清洗」共享同一份数据",
    "自定义处理": "通过动态 UI 进行复杂数据操作，无需编写代码",
}


def _render_file_upload():
    """统一渲染文件上传区域，支持多文件和多sheet选择"""
    df_key = f"{PREFIX}_df"
    all_key = f"{PREFIX}_all_dfs"
    
    uploaded_df = handle_file_upload(PREFIX, "上传原始报表")
    
    all_dfs = st.session_state.get(all_key, {})
    
    st.subheader("📋 选择处理对象")
    uploaded_df = render_sheet_selector(PREFIX, all_dfs)
    
    if uploaded_df is not None:
        st.success(f"当前数据：{len(uploaded_df)} 行 × {len(uploaded_df.columns)} 列")
        with st.expander("数据预览", expanded=False):
            st.dataframe(uploaded_df.head(10), use_container_width=True)
    return uploaded_df


def _render_ai_cleaning(df):
    """AI智能清洗功能"""
    messages_key = f"{PREFIX}_messages"
    
    for message in st.session_state[messages_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "df" in message:
                st.dataframe(message["df"].head(), use_container_width=True)

    if prompt := st.chat_input(
        "请输入清洗指令（例如：删除空值，将日期格式化）",
        disabled=df is None,
    ):
        if df is None:
            st.warning("请先在上方上传表格文件！")
            return

        st.session_state[messages_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        current_df = df
        df_info = (
            f"当前表格列名：{list(current_df.columns)}\n"
            f"前5行数据预览：\n{current_df.head().to_string()}"
        )

        system_prompt = f"""你是一个 Pandas 数据清洗专家。用户会给你一段表格信息和清洗需求。
{df_info}
请直接输出可执行的 Python Pandas 代码，不要包含任何解释文字。代码必须使用变量名 `df` 代表当前表格，并将清洗后的结果赋值给 `df_cleaned`。
例如：
```python
df_cleaned = df.dropna()
```"""

        with st.chat_message("assistant"):
            with st.spinner("AI 正在思考并生成代码..."):
                try:
                    ai_service = get_ai_service()
                    if not ai_service.api_key and ai_service.provider != "Ollama":
                        st.warning("请先在AI服务配置中填写API Key")
                        st.info("可用配置方式：")
                        st.info("1. 选择OpenAI并填写API Key")
                        st.info("2. 选择Anthropic并填写API Key")
                        st.info("3. 选择Gemini并填写API Key")
                        st.info("4. 选择Ollama（需要本地安装）")
                        st.session_state[messages_key].append({"role": "assistant", "content": "⚠️ 请先配置AI服务"})
                        return
                    
                    response = ai_service.chat(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        model=st.session_state.get("ai_model", "gpt-4o-mini"),
                        temperature=0.7,
                    )
                    if response is None:
                        st.error("AI服务调用失败，请检查网络连接和API配置")
                        return
                    ai_code = (
                        response
                        .strip()
                        .replace("```python", "")
                        .replace("```", "")
                    )

                    local_vars = {"df": current_df.copy(), "pd": pd}
                    exec(ai_code, {}, local_vars)
                    df_result = local_vars.get("df_cleaned", current_df)

                    st.markdown(f"✅ **AI 执行成功！** 处理后剩余 {len(df_result)} 行数据。")
                    st.code(ai_code, language="python")
                    st.dataframe(df_result.head(), use_container_width=True)

                    st.session_state[messages_key].append(
                        {
                            "role": "assistant",
                            "content": f"✅ **清洗完成！** 处理后剩余 {len(df_result)} 行数据。",
                            "df": df_result,
                        }
                    )
                    st.session_state[f"{PREFIX}_df"] = df_result

                except Exception as e:
                    error_msg = f"❌ AI 生成的代码执行报错：{str(e)}"
                    st.error(error_msg)
                    st.session_state[messages_key].append({"role": "assistant", "content": error_msg})


def run(page_name: Optional[str] = None):
    if page_name is None:
        page_name = st.session_state.get("nav_page", "AI 智能清洗")
    
    st.title(PAGE_TITLES.get(page_name, "数据处理"))
    st.caption(PAGE_CAPTIONS.get(page_name, ""))
    
    init_module_state(PREFIX, {"messages": []})
    
    df = _render_file_upload()
    
    st.divider()
    
    if page_name == "AI 智能清洗":
        _render_ai_cleaning(df)
    elif page_name == "常规表格处理":
        mod1_table_general_processor.run(df)
    elif page_name == "自定义处理":
        mod1_table_general_processor.render_custom_processing(df)
    
    if df is not None:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 存入数据库", key=f"{PREFIX}_save_db"):
                save_to_db(df, "processed_data")
                st.success("数据已安全入库！")
        with col2:
            output = io.BytesIO()
            df.to_excel(output, index=False)
            st.download_button(
                label="📥 导出为 Excel",
                data=output.getvalue(),
                file_name="processed_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{PREFIX}_export",
            )

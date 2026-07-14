import streamlit as st
import pandas as pd
import ollama
from utils.db_manager import save_to_db

def run():
    st.title("🧹 模块一：AI 智能数据清洗工作台")
    
    # 1. 初始化会话状态（用于记忆对话历史和当前表格数据）
    if "clean_messages" not in st.session_state:
        st.session_state.clean_messages = []
    if "current_df" not in st.session_state:
        st.session_state.current_df = None

    # 2. 独立上传区域
    uploaded_file = st.file_uploader("📂 上传原始报表", type=["xlsx", "csv"], key="etl_upload")
    if uploaded_file:
        if uploaded_file.name.endswith('.xlsx'):
            st.session_state.current_df = pd.read_excel(uploaded_file)
        else:
            st.session_state.current_df = pd.read_csv(uploaded_file)
        st.success(f"成功加载：{uploaded_file.name}，共 {len(st.session_state.current_df)} 行数据")

    # 3. 历史对话展示区
    for message in st.session_state.clean_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # 如果 AI 回复中包含处理后的数据，展示出来
            if "df" in message:
                st.dataframe(message["df"].head(), use_container_width=True)

    # 4. 底部对话框（只有上传了表格才能对话）
    if prompt := st.chat_input("请输入清洗指令（例如：删除空值，将日期格式化）", disabled=st.session_state.current_df is None):
        # 如果没上传表格就提示
        if st.session_state.current_df is None:
            st.warning("请先在上方上传表格文件！")
            return

        # 将用户输入加入历史
        st.session_state.clean_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 5. 核心：拼接 Prompt 发送给 Ollama
        # 把表格的列名和前5行数据给 AI，让它知道自己在处理什么
        df_info = f"当前表格列名：{list(st.session_state.current_df.columns)}\n前5行数据预览：\n{st.session_state.current_df.head().to_string()}"
        
        system_prompt = f"""你是一个 Pandas 数据清洗专家。用户会给你一段表格信息和清洗需求。
{df_info}
请直接输出可执行的 Python Pandas 代码，不要包含任何解释文字。代码必须使用变量名 `df` 代表当前表格，并将清洗后的结果赋值给 `df_cleaned`。
例如：
```python
df_cleaned = df.dropna()
```"""
        
        # 6. 调用本地 Ollama
        with st.chat_message("assistant"):
            with st.spinner("AI 正在思考并生成代码..."):
                try:
                    response = ollama.chat(
                        model="qwen2.5", # 确保与你本地 Ollama 模型名一致
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ai_code = response['message']['content'].strip().replace("```python", "").replace("```", "")
                    
                    # 7. 安全执行 AI 生成的代码
                    local_vars = {"df": st.session_state.current_df.copy(), "pd": pd}
                    exec(ai_code, {}, local_vars)
                    df_result = local_vars.get("df_cleaned", st.session_state.current_df)
                    
                    st.markdown(f"✅ **AI 执行成功！** 处理后剩余 {len(df_result)} 行数据。")
                    st.code(ai_code, language="python") # 展示 AI 写的代码
                    st.dataframe(df_result.head(), use_container_width=True)
                    
                    # 将结果存入历史记忆
                    st.session_state.clean_messages.append({
                        "role": "assistant", 
                        "content": f"✅ **清洗完成！** 处理后剩余 {len(df_result)} 行数据。",
                        "df": df_result
                    })
                    # 更新当前表格为清洗后的表格（支持连续对话清洗）
                    st.session_state.current_df = df_result
                    
                except Exception as e:
                    error_msg = f"❌ AI 生成的代码执行报错：{str(e)}"
                    st.error(error_msg)
                    st.session_state.clean_messages.append({"role": "assistant", "content": error_msg})

    # 8. 独立存库与导出区域
    if st.session_state.current_df is not None:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 存入数据库"):
                save_to_db(st.session_state.current_df, "cleaned_data")
                st.success("数据已安全入库！")
        with col2:
            if st.button("📥 导出为 Excel"):
                # 将 DataFrame 转为 Excel 二进制流
                import io
                output = io.BytesIO()
                st.session_state.current_df.to_excel(output, index=False)
                st.download_button(
                    label="⬇️ 点击下载文件",
                    data=output.getvalue(),
                    file_name="cleaned_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
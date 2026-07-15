import pandas as pd
import streamlit as st

from utils.ai_service import get_ai_service
from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state, render_sheet_selector

PREFIX = "module2"


def _detect_anomalies(df, row_fields, col_fields):
    result = []

    for col in col_fields:
        if df[col].dtype in ['int64', 'float64']:
            mean_val = df[col].mean()
            std_val = df[col].std()
            threshold = 3
            anomalies = df[(df[col] - mean_val).abs() > threshold * std_val]

            if not anomalies.empty:
                for _, row in anomalies.iterrows():
                    row_info = ", ".join([f"{f}: {row[f]}" for f in row_fields]) if row_fields else f"行索引: {row.name}"
                    result.append({
                        "行信息": row_info,
                        "异常字段": col,
                        "异常值": row[col],
                        "平均值": round(mean_val, 2),
                        "标准差": round(std_val, 2),
                        "偏差倍数": round(abs(row[col] - mean_val) / std_val, 2),
                    })

    return pd.DataFrame(result)


def run():
    st.title("🧠 AI 异常分析")
    st.caption("上传报表数据，选择字段进行异常检测")

    init_module_state(PREFIX, {"prompt": "请分析以下数据的异常指标", "result": None})

    df_key = f"{PREFIX}_df"
    all_key = f"{PREFIX}_all_dfs"
    prompt_key = f"{PREFIX}_prompt"
    result_key = f"{PREFIX}_result"

    uploaded_df = handle_file_upload(PREFIX, "上传待分析报表")
    
    all_dfs = st.session_state.get(all_key, {})
    
    st.subheader("📋 选择处理对象")
    uploaded_df = render_sheet_selector(PREFIX, all_dfs)

    if uploaded_df is not None:
        st.success(f"当前数据：{len(uploaded_df)} 行 × {len(uploaded_df.columns)} 列")

    df = uploaded_df
    if df is not None:
        with st.expander("数据预览", expanded=False):
            st.dataframe(df.head(10), use_container_width=True)

        columns = list(df.columns)
        numeric_cols = [c for c in columns if df[c].dtype in ['int64', 'float64']]

        st.subheader("字段选择")
        col1, col2 = st.columns(2)
        with col1:
            row_fields = st.multiselect("行标题字段", options=columns, key=f"{PREFIX}_row_fields")
        with col2:
            col_fields = st.multiselect(
                "列标题字段（待分析数值字段）",
                options=numeric_cols,
                default=numeric_cols[:3] if numeric_cols else [],
                key=f"{PREFIX}_col_fields"
            )

        st.subheader("分析参数")
        threshold = st.slider("异常检测阈值（标准差倍数）", min_value=1.0, max_value=5.0, value=3.0, step=0.5, key=f"{PREFIX}_threshold")

        st.session_state[prompt_key] = st.text_area(
            "自定义分析指令",
            value=st.session_state[prompt_key],
            key=f"{PREFIX}_prompt_input",
            placeholder="输入额外的分析要求，例如：重点关注负值异常"
        )

        analysis_mode = st.radio("分析模式", ["算法检测", "AI智能分析"], key=f"{PREFIX}_analysis_mode", horizontal=True)

        if st.button("开始分析", key=f"{PREFIX}_run", type="primary"):
            save_to_db(df, "analysis_data")

            if analysis_mode == "算法检测":
                with st.spinner("正在检测异常..."):
                    anomaly_df = _detect_anomalies(df, row_fields, col_fields)

                if anomaly_df.empty:
                    st.success("✅ 未检测到异常数据")
                    st.session_state[result_key] = None
                else:
                    st.warning(f"⚠️ 检测到 {len(anomaly_df)} 条异常数据")
                    st.session_state[result_key] = anomaly_df
            else:
                with st.spinner("AI 正在分析..."):
                    ai_service = get_ai_service()
                    df_info = (
                        f"表格列名：{list(df.columns)}\n"
                        f"数据行数：{len(df)}\n"
                        f"行标题字段：{row_fields}\n"
                        f"分析字段：{col_fields}\n"
                        f"前10行数据：\n{df.head(10).to_string()}"
                    )
                    response = ai_service.chat(
                        messages=[
                            {"role": "system", "content": "你是一个数据分析师，请分析以下数据中的异常值，并给出详细的分析报告。"},
                            {"role": "user", "content": f"{df_info}\n\n请分析以上数据的异常指标，并给出详细的分析报告。"},
                        ],
                        temperature=0.5,
                    )
                    if response:
                        st.session_state[result_key] = {"type": "ai_report", "content": response}
                    else:
                        st.error("AI分析失败")

        result = st.session_state.get(result_key)
        if isinstance(result, pd.DataFrame):
            st.subheader("异常分析结果")
            st.dataframe(result, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                output = pd.io.common.StringIO()
                result.to_csv(output, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="导出异常报告（CSV）",
                    data=output.getvalue(),
                    file_name="anomaly_report.csv",
                    mime="text/csv",
                    key=f"{PREFIX}_export_csv"
                )
            with col2:
                import io
                output_xlsx = io.BytesIO()
                with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
                    result.to_excel(writer, index=False, sheet_name='异常数据')
                    df.to_excel(writer, index=False, sheet_name='原始数据')
                output_xlsx.seek(0)
                st.download_button(
                    label="导出异常报告（Excel）",
                    data=output_xlsx.getvalue(),
                    file_name="anomaly_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"{PREFIX}_export_xlsx"
                )
        elif isinstance(result, dict) and result.get("type") == "ai_report":
            st.subheader("AI 分析报告")
            st.markdown(result["content"])

    st.divider()
    st.info("💡 提示：异常检测采用3σ原则，即超过平均值3倍标准差的数据判定为异常")

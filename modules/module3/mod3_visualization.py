import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.db_manager import save_to_db
from utils.file_ops import handle_file_upload, init_module_state, render_sheet_selector

PREFIX = "module3"


def run():
    st.title("📊 数据可视化")
    st.caption("选择图表类型和字段，快速生成多种可视化图表")

    init_module_state(PREFIX, {"x_col": None, "y_cols": [], "chart_type": "柱状图", "chart_generated": False})

    df_key = f"{PREFIX}_df"
    all_key = f"{PREFIX}_all_dfs"
    x_key = f"{PREFIX}_x_col"
    y_key = f"{PREFIX}_y_cols"
    chart_type_key = f"{PREFIX}_chart_type"
    chart_key = f"{PREFIX}_chart_generated"

    uploaded_df = handle_file_upload(PREFIX, "上传绘图数据")
    
    all_dfs = st.session_state.get(all_key, {})
    
    st.subheader("📋 选择处理对象")
    uploaded_df = render_sheet_selector(PREFIX, all_dfs)

    if uploaded_df is not None:
        st.success(f"当前数据：{len(uploaded_df)} 行 × {len(uploaded_df.columns)} 列")

    df = st.session_state.get(df_key)
    if df is not None:
        with st.expander("数据预览", expanded=False):
            st.dataframe(df.head(10), use_container_width=True)

        save_to_db(df, "viz_data")

        columns = list(df.columns)
        numeric_cols = [c for c in columns if df[c].dtype in ['int64', 'float64']]

        st.subheader("图表配置")

        col1, col2 = st.columns(2)
        with col1:
            chart_type = st.selectbox(
                "图表类型",
                ["柱状图", "条形图", "折线图", "饼图", "综合图"],
                key=chart_type_key
            )
        with col2:
            x_col = st.selectbox(
                "X 轴字段",
                options=columns,
                key=f"{PREFIX}_x"
            )

        y_cols = st.multiselect(
            "Y 轴字段（可多选）",
            options=numeric_cols,
            default=numeric_cols[:2] if numeric_cols else [],
            key=f"{PREFIX}_y"
        )

        if chart_type == "综合图":
            combined_types = st.multiselect(
                "选择组合图表类型",
                ["柱状图", "条形图", "折线图"],
                default=["柱状图", "折线图"],
                key=f"{PREFIX}_combined_types"
            )

        if st.button("生成图表", key=f"{PREFIX}_chart", type="primary"):
            st.session_state[chart_key] = True

        if st.session_state.get(chart_key):
            st.subheader("图表预览")

            try:
                if chart_type == "柱状图":
                    fig = px.bar(df, x=x_col, y=y_cols, barmode='group', title=f'{x_col} 柱状图')
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "条形图":
                    fig = px.bar(df, x=x_col, y=y_cols, barmode='group', orientation='h', title=f'{x_col} 条形图')
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "折线图":
                    fig = px.line(df, x=x_col, y=y_cols, title=f'{x_col} 折线图', markers=True)
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "饼图":
                    if y_cols:
                        fig = px.pie(df, values=y_cols[0], names=x_col, title=f'{y_cols[0]} 分布饼图')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("请选择至少一个Y轴字段")

                elif chart_type == "综合图":
                    fig = go.Figure()
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

                    for i, y_col in enumerate(y_cols):
                        if "柱状图" in combined_types:
                            fig.add_trace(go.Bar(x=df[x_col], y=df[y_col], name=f'{y_col} (柱状)', marker_color=colors[i % len(colors)]))
                        if "折线图" in combined_types:
                            fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], name=f'{y_col} (折线)', mode='lines+markers', line=dict(color=colors[i % len(colors)])))
                        if "条形图" in combined_types:
                            fig.add_trace(go.Bar(x=df[x_col], y=df[y_col], name=f'{y_col} (条形)', marker_color=colors[i % len(colors)]))

                    fig.update_layout(title=f'{x_col} 综合图', barmode='group')
                    st.plotly_chart(fig, use_container_width=True)

                output_html = fig.to_html(full_html=False)
                st.download_button(
                    label="导出图表为HTML",
                    data=output_html,
                    file_name=f"{x_col}_chart.html",
                    mime="text/html",
                    key=f"{PREFIX}_export_html"
                )

                try:
                    output_png = io.BytesIO()
                    fig.write_image(output_png, format='png', width=1200, height=600)
                    output_png.seek(0)
                    st.download_button(
                        label="导出图表为PNG图片",
                        data=output_png.getvalue(),
                        file_name=f"{x_col}_chart.png",
                        mime="image/png",
                        key=f"{PREFIX}_export_png"
                    )
                except Exception:
                    st.info("提示：PNG导出需要安装kaleido库，当前仅支持HTML导出")

            except Exception as e:
                st.error(f"图表生成失败：{str(e)}")

    st.divider()
    st.info("💡 提示：综合图支持同时展示柱状图、折线图等多种图表类型")

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.parser import parse_table_text, parse_yaml_text
from src.validators import validate_tasks
from src.gantt_plotly import create_gantt_figure, auto_view_mode
from src.gantt_mermaid import generate_mermaid_code
from src.export_excel import export_tasks_to_excel, export_tasks_to_csv
from src.export_static import export_plotly_figure
from src.project_manager import list_projects, load_project, save_project, delete_project, create_default_project
from src.llm_client import generate_gantt_data
from src.api_config import load_api_config, save_api_config

DEFAULT_TABLE_TEXT = """任务名 | 开始 | 结束 | 分组 | 状态 | 进度 | 依赖
整理 APG 数据 | 2026-06-01 | 2026-06-05 | 数据处理 | done | 100 |
清洗 y+ 数据 | 2026-06-06 | 2026-06-08 | 数据处理 | active | 60 | 整理 APG 数据
跑 PSRN 主实验 | 2026-06-09 | 2026-06-15 | 符号回归 | active | 20 | 清洗 y+ 数据
分析 Pareto front | 2026-06-16 | 2026-06-18 | 符号回归 | pending | 0 | 跑 PSRN 主实验
画论文图 | 2026-06-19 | 2026-06-23 | 论文写作 | pending | 0 | 分析 Pareto front"""

DEFAULT_YAML_TEXT = """project: 论文实验计划
date_format: YYYY-MM-DD

tasks:
  - name: 整理 APG 数据
    start: 2026-06-01
    end: 2026-06-05
    group: 数据处理
    status: done
    progress: 100

  - name: 清洗 y+ 数据
    start: 2026-06-06
    end: 2026-06-08
    group: 数据处理
    status: active
    progress: 60
    depends_on: 整理 APG 数据

  - name: 跑 PSRN 主实验
    start: 2026-06-09
    end: 2026-06-15
    group: 符号回归
    status: active
    progress: 20
    depends_on: 清洗 y+ 数据

  - name: 分析 Pareto front
    start: 2026-06-16
    end: 2026-06-18
    group: 符号回归
    status: pending
    progress: 0
    depends_on: 跑 PSRN 主实验

  - name: 画论文图
    start: 2026-06-19
    end: 2026-06-23
    group: 论文写作
    status: pending
    progress: 0
    depends_on: 分析 Pareto front"""

PAGE_CSS = """
<style>
    header[data-testid="stHeader"] { background: transparent; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%); }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); }
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] .stCaption { color: #c8d6e5 !important; }
    section[data-testid="stSidebar"] .stSubheader { color: #e0e6ed !important; }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 { color: #f0f3f7 !important; }
    section[data-testid="stSidebar"] [data-testid="stDivider"] { border-color: rgba(255,255,255,0.12); }
    div.stButton > button { 
        border-radius: 8px; font-weight: 600; transition: all 0.2s;
        border: none;
    }
    div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0; padding: 10px 24px;
        font-weight: 600; font-size: 15px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    .download-grid {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
        margin-top: 12px;
    }
    .metric-card {
        background: white; border-radius: 12px; padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 12px;
    }
</style>
"""


def init_session_state():
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'project_name' not in st.session_state:
        st.session_state.project_name = "论文实验计划"
    if 'input_format' not in st.session_state:
        st.session_state.input_format = "Table"
    if 'input_text' not in st.session_state:
        st.session_state.input_text = DEFAULT_TABLE_TEXT
    if 'ai_api_base' not in st.session_state:
        saved = load_api_config()
        st.session_state.ai_api_base = saved.get("api_base", "https://api.openai.com/v1")
        st.session_state.ai_api_key = saved.get("api_key", "")
        st.session_state.ai_model = saved.get("model", "gpt-4o-mini")
    if 'parsed_df' not in st.session_state:
        st.session_state.parsed_df = None
    if 'mermaid_code' not in st.session_state:
        st.session_state.mermaid_code = ""
    if 'fig' not in st.session_state:
        st.session_state.fig = None


def load_project_data(project_name):
    project_data = load_project(project_name)
    if project_data:
        st.session_state.project_name = project_data.get('name', project_name)
        st.session_state.input_format = project_data.get('format', 'Table')
        st.session_state.input_text = project_data.get('content', '')
        st.session_state.current_project = project_name


def parse_and_validate(input_text, input_format):
    if not input_text or input_text.strip() == "":
        return None, None, ["Please input task data."]

    try:
        if input_format == "Table":
            df = parse_table_text(input_text)
        else:
            df = parse_yaml_text(input_text)
    except ValueError as e:
        return None, None, [str(e)]
    except Exception as e:
        return None, None, [f"Parse error: {str(e)}"]

    validation_results = validate_tasks(df)
    errors = [r for r in validation_results if not r.startswith("Warning")]
    warnings = [r for r in validation_results if r.startswith("Warning")]

    if errors:
        return None, None, errors

    return df, warnings, None


def main():
    st.set_page_config(page_title="Gantt Chart Generator", layout="wide", page_icon="📊")
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

    init_session_state()

    with st.sidebar:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:28px;">📊</span>
            <span style="font-size:20px;font-weight:700;color:#f0f3f7;">Gantt Generator</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Task-to-chart in one click")

        st.divider()

        st.subheader("📁 Project")

        projects = list_projects()
        if projects:
            selected_project = st.selectbox(
                "Select Project",
                options=[""] + projects,
                index=0 if not st.session_state.current_project else (
                    projects.index(st.session_state.current_project) + 1
                    if st.session_state.current_project in projects else 0
                ),
                label_visibility="collapsed",
            )
            if selected_project and selected_project != st.session_state.current_project:
                load_project_data(selected_project)
                st.rerun()
        else:
            st.info("No saved projects yet.")

        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("➕ New", use_container_width=True, help="Create a new project"):
                new_name = create_default_project()
                load_project_data(new_name)
                st.rerun()
        with col_btn2:
            if st.button("💾 Save", use_container_width=True, help="Save current project"):
                if st.session_state.project_name:
                    save_project(st.session_state.project_name, st.session_state.input_format, st.session_state.input_text)
                    st.toast(f"✅ '{st.session_state.project_name}' saved", icon="💾")
                    st.rerun()
        with col_btn3:
            if st.button("🗑️ Del", use_container_width=True, help="Delete current project"):
                if st.session_state.current_project:
                    delete_project(st.session_state.current_project)
                    st.session_state.current_project = None
                    st.session_state.project_name = "论文实验计划"
                    st.session_state.input_format = "Table"
                    st.session_state.input_text = DEFAULT_TABLE_TEXT
                    st.toast("Project deleted", icon="🗑️")
                    st.rerun()

        st.divider()

        project_name = st.text_input("Project Name", value=st.session_state.project_name, key="project_name_input")
        st.session_state.project_name = project_name

        input_format = st.selectbox("Input Format", ["Table", "YAML"], index=0 if st.session_state.input_format == "Table" else 1)
        st.session_state.input_format = input_format

        st.divider()

        st.subheader("⚙️ View Settings")

        view_mode_options = ["Day", "Week", "Month", "Auto"]
        view_mode = st.selectbox("Time Scale", view_mode_options)
        show_progress = st.checkbox("Show Progress Bar", value=True)
        show_today = st.checkbox("Show Today Line", value=True)

        st.divider()

        with st.expander("🤖 AI Generate", expanded=False):
            st.caption("Describe your plan in natural language.")

            ai_api_base = st.text_input("API Base URL", value=st.session_state.ai_api_base, key="ai_api_base_input", placeholder="https://api.openai.com/v1")
            st.session_state.ai_api_base = ai_api_base

            col_key, col_model = st.columns(2)
            with col_key:
                ai_api_key = st.text_input("API Key", type="password", value=st.session_state.ai_api_key, key="ai_api_key_input")
                st.session_state.ai_api_key = ai_api_key
            with col_model:
                ai_model = st.text_input("Model", value=st.session_state.ai_model, key="ai_model_input", placeholder="gpt-4o-mini")
                st.session_state.ai_model = ai_model

            col_save1, col_save2 = st.columns([1, 3])
            with col_save1:
                if st.button("💾 Save Config", key="save_api_config_btn"):
                    save_api_config(st.session_state.ai_api_base, st.session_state.ai_api_key, st.session_state.ai_model)
                    st.toast("API config saved", icon="💾")

            nl_prompt = st.text_area("Describe your project plan", placeholder="e.g.: 帮我创建一个3个月的软件开发项目计划，包含需求分析、UI设计、后端开发、前端开发、集成测试和上线部署六个阶段", height=100, key="nl_prompt_input")

            col_gen1, col_gen2 = st.columns([1, 2])
            with col_gen1:
                gen_fmt = st.selectbox("Output Format", ["Table", "YAML"], key="gen_fmt")
            with col_gen2:
                gen_button = st.button("✨ Generate with AI", type="secondary", use_container_width=True)

            if gen_button:
                if not nl_prompt or nl_prompt.strip() == "":
                    st.warning("Please describe your project plan first.")
                elif not ai_api_key or ai_api_key.strip() == "":
                    st.warning("Please enter your API Key first.")
                else:
                    with st.spinner("AI is generating task data..."):
                        try:
                            result = generate_gantt_data(api_base=ai_api_base, api_key=ai_api_key, model=ai_model, user_prompt=nl_prompt, fmt=gen_fmt)
                            st.session_state.input_text = result
                            st.session_state.input_format = gen_fmt
                            st.rerun()
                        except Exception as e:
                            st.error(f"Generation failed: {str(e)}")

        if input_format == "Table":
            default_text = DEFAULT_TABLE_TEXT
        else:
            default_text = DEFAULT_YAML_TEXT

        input_text = st.text_area("Task Data", value=st.session_state.input_text if st.session_state.input_text else default_text, height=260, key="task_data_input")
        st.session_state.input_text = input_text

        parse_button = st.button("🚀 Parse / Generate", type="primary", use_container_width=True)

        if parse_button:
            df, warnings, errors = parse_and_validate(input_text, input_format)
            if errors:
                for error in errors:
                    st.error(error)
                st.session_state.parsed_df = None
            else:
                st.session_state.parsed_df = df

                if view_mode == "Auto":
                    effective_view_mode = auto_view_mode(df)
                else:
                    effective_view_mode = view_mode

                st.session_state.mermaid_code = generate_mermaid_code(df, project_name, effective_view_mode, show_progress, show_today)
                st.session_state.fig = create_gantt_figure(df, project_name, effective_view_mode, show_progress, show_today)

                if warnings:
                    for warning in warnings:
                        st.warning(warning)
                st.toast("✅ Chart generated", icon="📊")
                st.rerun()

    st.title("📊 Gantt Chart Generator")
    st.caption("Visualize your project timeline — paste task data → get beautiful Gantt charts")

    df = st.session_state.parsed_df

    if df is None:
        st.info("👈 Fill in your task data in the sidebar and click **Parse / Generate** to get started.")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["📈 Preview", "📋 Task Data", "📝 Mermaid Code", "⬇️ Downloads"])

    with tab1:
        st.plotly_chart(st.session_state.fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

    with tab2:
        display_df = df.copy()
        display_df['start'] = display_df['start'].dt.strftime('%Y-%m-%d')
        display_df['end'] = display_df['end'].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df, use_container_width=True, height=(len(df) + 1) * 35 + 38)

    with tab3:
        st.code(st.session_state.mermaid_code, language="mermaid", line_numbers=False)
        mermaid_md = f"```mermaid\n{st.session_state.mermaid_code}\n```"
        st.download_button(label="📥 Download Markdown", data=mermaid_md.encode('utf-8'), file_name="gantt.md", mime="text/markdown", type="primary")

    with tab4:
        fig = st.session_state.fig
        mermaid_code = st.session_state.mermaid_code

        csv_data = export_tasks_to_csv(df)
        mermaid_md = f"```mermaid\n{mermaid_code}\n```"
        html_content = fig.to_html(include_plotlyjs=True, full_html=True)
        excel_data = export_tasks_to_excel(df)
        export_html = export_plotly_figure(fig, "png")

        st.markdown("""
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:8px;">
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.download_button(label="📊 CSV", data=csv_data, file_name="tasks.csv", mime="text/csv", use_container_width=True, type="primary")
        with col_b:
            st.download_button(label="📝 Markdown", data=mermaid_md.encode('utf-8'), file_name="gantt.md", mime="text/markdown", use_container_width=True, type="primary")
        with col_c:
            st.download_button(label="🌐 HTML", data=html_content.encode('utf-8'), file_name="gantt.html", mime="text/html", use_container_width=True, type="primary")

        col_d, col_e, col_f = st.columns(3)
        with col_d:
            st.download_button(label="📗 Excel", data=excel_data, file_name="tasks.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with col_e:
            st.download_button(label="🖼️ PNG Export", data=export_html, file_name="gantt-export.html", mime="text/html", use_container_width=True)
        with col_f:
            st.download_button(label="📄 PDF Export", data=export_html, file_name="gantt-export.html", mime="text/html", use_container_width=True)


if __name__ == "__main__":
    main()
# 📊 Gantt Chart Generator

一个基于 Streamlit 的本地甘特图生成器，支持从表格/YAML 输入快速生成交互式甘特图。

## ✨ 功能特点

- 🎯 **多格式输入**：支持表格文本（pipe-separated）和 YAML 格式
- 📈 **交互式预览**：使用 Plotly 生成可交互的甘特图
- 📝 **Mermaid 代码**：自动生成可复制到 Markdown 的 Mermaid Gantt 代码
- 📥 **多格式导出**：支持 CSV、Excel、HTML、Markdown 导出
- 🤖 **AI 辅助生成**：支持自然语言描述自动生成任务计划
- 🔍 **视图切换**：日/周/月视图及自动适配
- 📅 **今日标记**：可切换显示今日日期线

## 🚀 快速开始

### 安装依赖

```bash
pip install -r gantt_generator/requirements.txt
```

### 启动方式

**方式一：直接运行**

```bash
cd gantt_generator
streamlit run app.py
```

**方式二：双击启动脚本**（Windows）

```
启动甘特图.bat
```

### 访问应用

浏览器自动打开 http://localhost:8501

## 📋 使用示例

### 输入格式 - 表格模式

```text
任务名 | 开始 | 结束 | 分组 | 状态 | 进度 | 依赖
需求分析 | 2026-06-01 | 2026-06-05 | 规划 | done | 100 |
系统设计 | 2026-06-06 | 2026-06-10 | 规划 | active | 80 | 需求分析
前端开发 | 2026-06-11 | 2026-06-18 | 开发 | active | 40 | 系统设计
```

### 输入格式 - YAML 模式

```yaml
project: 软件开发项目
date_format: YYYY-MM-DD

tasks:
  - name: 需求分析
    start: 2026-06-01
    end: 2026-06-05
    group: 规划
    status: done
    progress: 100

  - name: 系统设计
    start: 2026-06-06
    end: 2026-06-10
    group: 规划
    status: active
    progress: 80
    depends_on: 需求分析
```

## 🛠️ 技术栈

- **Streamlit** - 本地 Web 界面框架
- **Plotly** - 交互式图表库
- **Pandas** - 数据处理
- **OpenAI API** - AI 辅助生成（可选）
- **PyYAML** - YAML 解析
- **OpenPyXL** - Excel 导出

## 📁 项目结构

```
gantt_generator/
├── app.py              # 主应用入口
├── requirements.txt    # 依赖列表
├── examples/           # 示例数据
└── src/
    ├── parser.py       # 输入解析
    ├── gantt_plotly.py # Plotly 图表生成
    ├── gantt_mermaid.py # Mermaid 代码生成
    ├── export_excel.py  # Excel/CSV 导出
    ├── export_static.py # 静态图片导出
    ├── project_manager.py # 项目管理
    ├── llm_client.py    # AI 客户端
    ├── api_config.py    # API 配置
    └── validators.py    # 数据校验
```

## 📝 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 任务名 | string | ✓ | 任务名称 |
| 开始 | date | ✓ | 开始日期 (YYYY-MM-DD) |
| 结束 | date | ✓ | 结束日期 (YYYY-MM-DD) |
| 分组 | string | | 任务分组，默认 General |
| 状态 | string | | done/active/pending/critical/milestone |
| 进度 | int | | 0-100，默认 0 |
| 依赖 | string | | 前置任务名称 |

## 📄 许可证

MIT License

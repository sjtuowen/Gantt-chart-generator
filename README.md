# Gantt Chart Generator

一个基于 Streamlit 的本地甘特图生成器，支持表格文本或 YAML 输入，并生成可交互的 Plotly 甘特图、Mermaid 代码和多种导出文件。

## 已实现功能

- 表格文本输入：支持 pipe-separated 格式，允许 `group`、`status`、`progress`、`depends_on` 为空。
- YAML 输入：支持从 `tasks` 字段读取任务列表。
- Plotly 交互式预览：支持日、周、月和自动时间尺度。
- 进度条显示：普通任务按包含结束日的时间范围绘制，单日任务也能正常显示。
- Milestone 标记：`status: milestone` 的任务以菱形 marker 单独显示，不绘制普通任务条。
- Mermaid 代码导出：可下载 Markdown 文件。
- 数据导出：支持 CSV、Excel、HTML、Markdown。
- 静态图片导出：支持真正的 PNG 和 PDF 文件下载；页面按钮默认使用 Matplotlib 普通静态图导出，不依赖浏览器。
- AI 辅助生成：可通过兼容 OpenAI 的 API 从自然语言生成任务数据。
- 项目保存/加载：本地保存项目 YAML。

## 安装依赖

```bash
pip install -r gantt_generator/requirements.txt
```

PNG/PDF 下载按钮默认使用 Matplotlib 生成普通静态图片/PDF。项目中也保留了 Plotly + Kaleido 导出函数；如果改用 Kaleido，新版 Kaleido 还需要本机可用的 Chrome/Chromium。

## 启动

```bash
cd gantt_generator
streamlit run app.py
```

浏览器通常会自动打开：

```text
http://localhost:8501
```

Windows 也可以双击仓库根目录中的启动脚本。

## 表格输入示例

```text
任务名 | 开始 | 结束 | 分组 | 状态 | 进度 | 依赖
需求分析 | 2026-06-01 | 2026-06-05 | 规划 | done | 100 |
系统设计 | 2026-06-06 | 2026-06-10 | 规划 | active | 80 | 需求分析
发布里程碑 | 2026-06-20 | 2026-06-20 | 发布 | milestone | 0 | 系统设计
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| 任务名 | 是 | 任务名称 |
| 开始 | 是 | 开始日期，格式 `YYYY-MM-DD` |
| 结束 | 是 | 结束日期，格式 `YYYY-MM-DD` |
| 分组 | 否 | 为空时默认为 `General` |
| 状态 | 否 | `done`、`active`、`pending`、`critical`、`milestone` |
| 进度 | 否 | 0-100，为空时默认为 0 |
| 依赖 | 否 | 前置任务名称 |

## YAML 输入示例

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

  - name: 发布里程碑
    start: 2026-06-20
    end: 2026-06-20
    group: 发布
    status: milestone
    progress: 0
    depends_on: 需求分析
```

## 导出说明

- CSV：导出任务表。
- Excel：导出任务表为 `.xlsx`。
- HTML：导出可交互 Plotly 页面。
- Markdown：导出 Mermaid 代码块。
- PNG：下载 `gantt.png`，MIME 为 `image/png`。
- PDF：下载 `gantt.pdf`，MIME 为 `application/pdf`。

如果 PNG/PDF 导出失败，页面会显示友好提示。当前页面按钮优先走 Matplotlib 兜底导出，可避开 Kaleido/Chrome 超时问题。



## 技术栈

- Streamlit
- Pandas
- Plotly
- Kaleido
- Matplotlib
- OpenPyXL
- PyYAML
- OpenAI API compatible client

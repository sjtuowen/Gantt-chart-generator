import time
from datetime import date

from openai import OpenAI


RETRY_MAX = 2
TIMEOUT_SECONDS = 120


def build_system_prompt(fmt: str) -> str:
    today = date.today().isoformat()
    base_rules = f"""Gantt chart task generator. Output ONLY task data, no explanations or markdown fences.
Rules: Today={today}. Dates should be after {today} unless the user specifies otherwise. Task duration 2-14 days. Status: done/active/pending. Progress 0-100. 2-4 groups. depends_on=task name. 4-8 tasks."""

    if fmt == "Table":
        return (
            base_rules
            + """ Format: pipe-separated, first line=header.
任务名 | 开始 | 结束 | 分组 | 状态 | 进度 | 依赖
需求分析 | 2026-06-01 | 2026-06-05 | 规划 | done | 100 |
系统设计 | 2026-06-06 | 2026-06-10 | 规划 | active | 80 | 需求分析"""
        )

    if fmt == "YAML":
        return (
            base_rules
            + """ Format: YAML.
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
    depends_on: 需求分析"""
        )

    return base_rules


def parse_llm_response(raw: str, fmt: str) -> str:
    text = raw.strip()

    HEADER = "任务名 | 开始 | 结束 | 分组 | 状态 | 进度 | 依赖"

    if fmt == "Table":
        lines = text.split("\n")
        data_lines = []
        found_header = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "任务名" in line and "开始" in line and "结束" in line:
                found_header = True
                data_lines.append(HEADER)
            elif found_header and "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    data_lines.append(line)
            elif "|" in line and not found_header:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    data_lines.append(line)

        if not data_lines:
            for line in text.split("\n"):
                line = line.strip()
                if line and "|" in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        data_lines.append(line)

        if not data_lines:
            return text

        if not found_header:
            data_lines.insert(0, HEADER)

        return "\n".join(data_lines)

    if fmt == "YAML":
        lines = text.split("\n")
        start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("project:"):
                start = i
                break
        if start == 0:
            for i, line in enumerate(lines):
                if line.strip().startswith("tasks:"):
                    start = i - 1 if i > 0 else i
                    break

        yaml_lines = lines[start:]
        return "\n".join(yaml_lines)

    return text


def generate_gantt_data(
    api_base: str,
    api_key: str,
    model: str,
    user_prompt: str,
    fmt: str = "Table",
) -> str:
    client = OpenAI(
        base_url=api_base.rstrip("/"),
        api_key=api_key,
        timeout=TIMEOUT_SECONDS,
        max_retries=1,
    )

    system_prompt = build_system_prompt(fmt)

    last_error = None
    for attempt in range(RETRY_MAX + 1):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
                stream=True,
            )

            collected = []
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    collected.append(chunk.choices[0].delta.content)

            raw = "".join(collected)
            if not raw.strip():
                raise RuntimeError("Empty response from API.")
            return parse_llm_response(raw, fmt)
        except Exception as e:
            last_error = e
            if attempt < RETRY_MAX:
                time.sleep(2)
                continue

    msg = str(last_error)
    if "524" in msg:
        raise RuntimeError(
            "API proxy timeout (524). The proxy server took too long. Try: 1) use a faster model, 2) retry, 3) switch API proxy."
        )
    if "timed out" in msg.lower() or "timeout" in msg.lower():
        raise RuntimeError(
            f"API request timed out after {TIMEOUT_SECONDS}s. Please try again or check your network."
        )
    if (
        "401" in msg
        or "invalid api key" in msg.lower()
        or "incorrect api key" in msg.lower()
    ):
        raise RuntimeError("Invalid API Key. Please check your key and try again.")
    if "404" in msg or "not found" in msg.lower():
        raise RuntimeError("Model not found. Please check the Model name.")
    raise RuntimeError(f"API error: {msg}")

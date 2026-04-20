"""OpenAI Chat Completions 要求 tools[].function.name 匹配 ^[a-zA-Z0-9_-]+$。"""

from __future__ import annotations

import re
from typing import Set

# 与 OpenAI API 常见限制对齐
_MAX_LEN = 64


def sanitize_openai_tool_name(name: str, *, used: Set[str] | None = None) -> str:
    """
    将任意字符串规范为 OpenAI 允许的 tool 名；可选 used 集合内去重（原地 add）。
    """
    s = str(name).strip() if name is not None else ""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", s)
    safe = re.sub(r"_+", "_", safe).strip("_")
    if not safe:
        safe = "tool"
    if len(safe) > _MAX_LEN:
        safe = safe[:_MAX_LEN].rstrip("_") or "tool"

    if used is None:
        return safe

    candidate = safe
    n = 2
    while candidate in used:
        suffix = f"_{n}"
        room = _MAX_LEN - len(suffix)
        base = safe[:room] if room > 0 else "t"
        candidate = (base.rstrip("_") or "t") + suffix
        n += 1
    used.add(candidate)
    return candidate

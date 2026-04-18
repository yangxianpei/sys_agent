import json
from typing import Any
import pytz
from datetime import datetime, timedelta
from pydantic import Field, create_model
from langchain_core.tools import StructuredTool
import requests


def format_result(data):
    # 如果是字典，递归转成自然语言描述
    if isinstance(data, dict):
        parts = []
        for k, v in data.items():
            # 跳过无意义的key
            if k in ["id", "key", "identifier", "code"] and len(str(v)) > 10:
                continue
            # 递归格式化
            parts.append(f"{k}: {format_result(v)}")
        return " | ".join(parts)
    # 如果是列表，取出内容
    elif isinstance(data, list):
        return "；".join(
            [format_result(item) for item in data[:3]]
        )  # 最多取3条，避免太长
    # 基本类型直接转字符串
    else:
        return str(data)


def should_format_joke_response(base_url, path, result):
    if not isinstance(result, dict):
        return False
    host = str(base_url or "").lower()
    endpoint = str(path or "").lower()
    return "jokeapi.dev" in host and endpoint.startswith("/joke")


def is_json_equal(json1, json2):
    """
    忽略空格、缩进、顺序，判断两个 JSON 是否内容一致
    """
    try:
        # 解析成字典（自动忽略空格）
        d1 = json.loads(json1) if isinstance(json1, str) else json1
        d2 = json.loads(json2) if isinstance(json2, str) else json2

        # 序列化成标准格式（排序key，去掉多余空格）
        s1 = json.dumps(d1, sort_keys=True, ensure_ascii=False)
        s2 = json.dumps(d2, sort_keys=True, ensure_ascii=False)

        return s1 == s2
    except:
        return False


def _json_type_to_python(schema_type: str | None):
    mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    return mapping.get(str(schema_type or "").lower(), str)


def _build_args_schema(tool_name: str, params):
    fields = {}
    for p in params or []:
        name = p.get("name")
        if not name:
            continue
        schema = p.get("schema", {})
        py_type = _json_type_to_python(schema.get("type"))
        required = bool(p.get("required", False))
        default = ... if required else None
        desc = p.get("description", "")
        fields[name] = (py_type, Field(default=default, description=desc))
    model_name = f"{tool_name.title().replace('_', '')}Args"
    return create_model(model_name, **fields)


def create_tool(base_url, path, method, params, full_desc):
    tool_name = f"{method.lower()}_{path.strip('/').replace('/', '_') or 'root'}"
    args_schema = _build_args_schema(tool_name, params)

    async def _acall(**kwargs):
        url = base_url.rstrip("/") + path
        payload = dict(kwargs or {})

        try:
            if method.lower() == "get":
                resp = requests.get(url, params=payload, timeout=10)
            else:
                resp = requests.post(url, json=payload, timeout=10)

            resp.raise_for_status()
            result2 = resp.json()
            return result2

        except Exception as e:
            err = {"error": str(e)}
            return str(err), err

    return StructuredTool.from_function(
        func=None,
        coroutine=_acall,
        name=tool_name,
        description=full_desc,
        args_schema=args_schema,
        return_direct=False,
    )


def build_tools_from_openapi(openai_schema):
    tools = []
    base_url = openai_schema["servers"][0]["url"]

    # 遍历所有路径
    for path, methods in openai_schema["paths"].items():
        for method, detail in methods.items():
            # 提取基础信息
            summary = detail.get("summary", "")
            description = detail.get("description", "")
            params = detail.get("parameters", [])

            param_names = [p["name"] for p in params if p.get("name")]

            # 自动生成JSON格式示例（通用）
            param_example = {}
            for name in param_names:
                param_example[name] = f"请输入{name}"

            format_example = ""
            # 转成标准JSON字符串，给LLM看
            if len(param_example) > 0:
                format_example = json.dumps(param_example, ensure_ascii=False, indent=2)

            # 生成最终工具描述
            full_desc = f"""
接口: {method.upper()} {path}
摘要: {summary}
描述: {description}
必填参数: {format_example}

规则：
1. 先决定是否需要调用该工具
2. 调用后基于结果给出自然语言回答
3. 不要向用户原样输出工具原始JSON
"""
            tool = create_tool(
                base_url=base_url,
                path=path,
                method=method,
                params=params,
                full_desc=full_desc,
            )

            tools.append(tool)

    return tools


def get_beijing_time():
    # 设置北京时区
    beijing_tz = pytz.timezone("Asia/Shanghai")

    # 获取当前的北京时区时间
    current_bj_time = datetime.now(beijing_tz)
    formatted_time = current_bj_time.strftime("%Y-%m-%d %H:%M")

    return formatted_time


import re


def openapi_to_tools(openapi: dict):
    tools = []

    for path, methods in openapi.get("paths", {}).items():
        for method, detail in methods.items():

            # 1️⃣ 生成函数名（规范一点）
            clean_path = re.sub(r"{|}", "", path.strip("/").replace("/", "_"))
            name = f"{method.lower()}_{clean_path or 'root'}"

            # 2️⃣ 描述（增强）
            summary = detail.get("summary", "")
            description = detail.get("description", "")

            full_desc = f"{summary}。{description}。当用户询问相关信息时使用该工具。"

            # 3️⃣ 参数解析
            properties = {}
            required = []

            params = detail.get("parameters", [])

            for p in params:
                pname = p.get("name")
                if not pname:
                    continue

                schema = p.get("schema", {})
                ptype = schema.get("type", "string")

                properties[pname] = {
                    "type": ptype,
                    "description": f"{pname}，例如：示例值",
                }

                if p.get("required", False):
                    required.append(pname)

            # 4️⃣ 如果没有参数，也要给空结构
            parameters = {
                "type": "object",
                "properties": properties,
                "required": required,
            }

            # 5️⃣ 组装 tool
            tool = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": full_desc,
                    "parameters": parameters,
                },
            }

            tools.append(tool)

    return tools

from langchain.agents import create_agent
from langchain_community.utilities.openapi import OpenAPISpec
from langchain_openai import ChatOpenAI
import json
from dotenv import load_dotenv
from app.config import Config
from langchain_core.tools import Tool
import requests
import os
import asyncio


def should_format_joke_response(base_url, path, result):
    if not isinstance(result, dict):
        return False
    host = str(base_url or "").lower()
    endpoint = str(path or "").lower()
    return "jokeapi.dev" in host and endpoint.startswith("/joke")


def extract_human_readable_response(result):
    if not isinstance(result, dict):
        return result

    if {"setup", "delivery"}.issubset(result.keys()):
        setup = str(result.get("setup", "")).strip()
        delivery = str(result.get("delivery", "")).strip()
        return f"{setup}\n{delivery}".strip()

    if "joke" in result:
        return str(result.get("joke", "")).strip()

    return result


def create_tool(base_url: str, path: str, method: str, params: list, full_desc: str):

    def _call(*args, **kwargs):
        # 2️⃣ 拼 URL
        url = base_url.rstrip("/") + path

        print(args[0])
        # 4️⃣ 发请求
        try:
            if method.lower() == "get":
                if args[0]:
                    resp = requests.get(url, params=json.loads(args[0]), timeout=10)
                else:
                    resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            if should_format_joke_response(base_url, path, result):
                return extract_human_readable_response(result)
            return result

        except Exception as e:
            print(e)
            return {"error": str(e)}

    return Tool(
        name=path.replace("/", "_"),
        description=full_desc,
        func=_call,
    )


def build_tools_from_openapi(openapi_json):
    tools = []
    base_url = openapi_json["servers"][0]["url"]
    # 遍历所有路径
    for path, methods in openapi_json["paths"].items():
        for method, detail in methods.items():
            # 提取基础信息
            summary = detail.get("summary", "")
            description = detail.get("description", "")
            params = detail.get("parameters", [])

            # 🔥 核心修复：从参数字典里提取真正的参数名
            param_names = [p["name"] for p in params]  # 只取每个参数的name字段

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

                【重要规则】
                1. 必须严格按照以下JSON格式返回参数
                2. 只返回JSON，不要任何多余文字、解释、说明
                3. 直接替换示例中的值为实际参数
                4. 如果没有必填参数 params 返回 ""
                5. 调用工具时候传的参数遵守这个{format_example}
                    """.strip()
            tool = create_tool(
                base_url=base_url,
                path=path,
                method=method,
                params=params,
                full_desc=full_desc,
            )

            tools.append(tool)

    return tools


load_dotenv()
# ======================
# 这就是你提供的 OpenAPI Schema
# ======================
openapi_json = {
    "openapi": "3.1.0",
    "info": {"title": "获取笑话", "version": "1.0"},
    "servers": [{"url": "https://v2.jokeapi.dev"}],
    "paths": {
        "/joke/Any": {
            "get": {
                "summary": "获取笑话",
                "description": "随机返回一条笑话",
                "parameters": [],
                "responses": {"200": {"description": "OK"}},
            }
        }
    },
}

# ======================
# 1. 把你的 JSON 传给 OpenAPISpec
# ======================
tools = build_tools_from_openapi(openapi_json)

# ======================
# 2. 创建 LLM
# ======================
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID", "deepseek-chat"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0,
)

# ======================
# 3. 一行代码创建 Agent！
# 它会自动读取你的 OpenAPI 并生成工具
# ======================
agent = create_agent(model=llm, tools=tools)  # 显示调用过程

# ======================
# 4. 直接提问！Agent 自动调用天气接口
payload = {
    "messages": [
        {
            "role": "user",
            "content": "讲个笑话",
        },
    ]
}


async def main():
    result = await agent.ainvoke(payload)

    print("\n=== 最终回答 ===")
    print(result["messages"][-1].content)


# ======================


if __name__ == "__main__":
    asyncio.run(main())


# import json
# from langchain_core.tools import Tool
# import requests


# def format_result(data):
#     # 如果是字典，递归转成自然语言描述
#     if isinstance(data, dict):
#         parts = []
#         for k, v in data.items():
#             # 跳过无意义的key
#             if k in ["id", "key", "identifier", "code"] and len(str(v)) > 10:
#                 continue
#             # 递归格式化
#             parts.append(f"{k}: {format_result(v)}")
#         return " | ".join(parts)
#     # 如果是列表，取出内容
#     elif isinstance(data, list):
#         return "；".join(
#             [format_result(item) for item in data[:3]]
#         )  # 最多取3条，避免太长
#     # 基本类型直接转字符串
#     else:
#         return str(data)


# def should_format_joke_response(base_url, path, result):
#     if not isinstance(result, dict):
#         return False
#     host = str(base_url or "").lower()
#     endpoint = str(path or "").lower()
#     return "jokeapi.dev" in host and endpoint.startswith("/joke")


# def is_json_equal(json1, json2):
#     """
#     忽略空格、缩进、顺序，判断两个 JSON 是否内容一致
#     """
#     try:
#         # 解析成字典（自动忽略空格）
#         d1 = json.loads(json1) if isinstance(json1, str) else json1
#         d2 = json.loads(json2) if isinstance(json2, str) else json2

#         # 序列化成标准格式（排序key，去掉多余空格）
#         s1 = json.dumps(d1, sort_keys=True, ensure_ascii=False)
#         s2 = json.dumps(d2, sort_keys=True, ensure_ascii=False)

#         return s1 == s2
#     except:
#         return False


# def create_tool(base_url, path, method, params, full_desc, output_parser):

#     async def _acall(*args, **kwargs):
#         url = base_url.rstrip("/") + path
#         payload = {}
#         if args:
#             first = args[0]
#             if isinstance(first, dict):
#                 payload.update(first)
#             elif isinstance(first, str):
#                 try:
#                     parsed = json.loads(first)
#                     if isinstance(parsed, dict):
#                         payload.update(parsed)
#                 except Exception:
#                     pass
#         if kwargs:
#             payload.update(kwargs)

#         try:
#             if method.lower() == "get":
#                 resp = requests.get(url, params=payload, timeout=10)
#             else:
#                 resp = requests.post(url, json=payload, timeout=10)

#             resp.raise_for_status()
#             result2 = resp.json()
#             content = await output_parser(result2)
#             return content, result2

#         except Exception as e:
#             err = {"error": str(e)}
#             return str(err), err

#     return Tool(
#         name=path.replace("/", "_"),
#         description=full_desc,
#         func=None,
#         coroutine=_acall,
#         response_format="content_and_artifact",
#         return_direct=False,
#     )


# def build_tools_from_openapi(openai_schema, self):
#     tools = []
#     base_url = openai_schema["servers"][0]["url"]

#     async def output_parser(output_text):
#         # 工具输出做本地确定性格式化，避免工具内再次调用 LLM
#         # 导致与 agent 主回答重复。
#         if isinstance(output_text, str):
#             return output_text
#         if isinstance(output_text, (dict, list)):
#             return format_result(output_text)
#         return str(output_text)

#     # 遍历所有路径
#     for path, methods in openai_schema["paths"].items():
#         for method, detail in methods.items():
#             # 提取基础信息
#             summary = detail.get("summary", "")
#             description = detail.get("description", "")
#             params = detail.get("parameters", [])

#             # 🔥 核心修复：从参数字典里提取真正的参数名
#             param_names = [p["name"] for p in params]  # 只取每个参数的name字段

#             # 自动生成JSON格式示例（通用）
#             param_example = {}
#             for name in param_names:
#                 param_example[name] = f"请输入{name}"

#             format_example = ""
#             # 转成标准JSON字符串，给LLM看
#             if len(param_example) > 0:
#                 format_example = json.dumps(param_example, ensure_ascii=False, indent=2)

#             # 生成最终工具描述
#             full_desc = f"""
# 接口: {method.upper()} {path}
# 摘要: {summary}
# 描述: {description}
# 必填参数: {format_example}

# 规则：
# 1. 只用于生成工具参数JSON
# 2. 必须严格返回JSON
# 3. 不要输出任何解释或文字
# """
#             tool = create_tool(
#                 base_url=base_url,
#                 path=path,
#                 method=method,
#                 params=params,
#                 full_desc=full_desc,
#                 output_parser=output_parser,
#             )

#             tools.append(tool)

#     return tools

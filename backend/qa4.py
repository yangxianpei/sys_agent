import asyncio

from app.utils.mcp import list_tools_for_service


# =========================
# 1. MCP 配置
# =========================
mcp_config = {
    "mcpServers": {
        "12306": {
            "type": "streamable_http",
            "url": "https://mcp.api-inference.modelscope.net/d5bb133112f749/mcp",
        }
    }
}


def get_first_mcp_server(config: dict):
    servers = config.get("mcpServers", {})

    if not servers:
        return None
    name, server = next(iter(servers.items()))

    return {"name": name, "type": server.get("type"), "url": server.get("url")}


async def main():
    result = await list_tools_for_service(mcp_config)

    print("\n===== RESULT =====")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

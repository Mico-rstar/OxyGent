import asyncio
import os
from dotenv import load_dotenv

from oxygent import MAS, Config, oxy, OxyRequest
from prompts import BROWSER_TOOL_PROXY_DESC, BROWSER_SYSTEM_PROMPT

# 自动加载 .env 文件中的环境变量
load_dotenv()

Config.set_agent_llm_model("default_llm")

async def data_workflow(oxy_request: OxyRequest):
    import json

    query = oxy_request.get_query()
    print("-------------query-------------")
    print(query)

    try:
        # 将query转化为json对象
        query_data = json.loads(query)
        tool_name = query_data.get("tool", "")

        if not tool_name:
            return "错误：未指定浏览器操作工具"
        else:
            del query_data["tool"]
        

        # 代理调用浏览器工具
        response = await oxy_request.call(
            callee=tool_name,
            arguments=query_data
        )

        if response.state.name == "COMPLETED":
            return response.output
        else:
            return f"浏览器操作失败: {response.output}"

    except json.JSONDecodeError:
        return "错误：查询参数不是有效的JSON格式"
    except Exception as e:
        return f"执行浏览器操作时发生错误: {str(e)}"


oxy_space = [
    oxy.HttpLLM(
        name="chat_llm",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("DEFAULT_LLM_CHAT_MODEL_NAME"),
    ),
    oxy.HttpLLM(
        name="flash_llm",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("FLASH_LLM_MODEL_NAME"),
    ),
    oxy.StdioMCPClient(
        name="browser_tool",
        params={
            "command": "npx",
            "args": ["-y", "chrome-devtools-mcp@latest"]
            # "args": ["@browsermcp/mcp@latest"]
        },
        category="tool",
        class_name="StdioMCPClient",
        desc="Browser automation tools via MCP",
        desc_for_llm="Browser automation tools via MCP protocol"
    ),
    oxy.WorkflowAgent(
        name='browser_agent',
        desc=BROWSER_TOOL_PROXY_DESC,
        # sub_agents=['ner_agent', 'nen_agent'],
        tools = ["browser_tool"],
        func_workflow=data_workflow,
        llm_model='chat_llm',
        is_retain_master_short_memory=True,
        extra_permitted_tool_name_list=["browser_tool"]
    ),
    oxy.ReActAgent(
        is_master=True,
        name="master_agent",
        prompt=BROWSER_SYSTEM_PROMPT,
        llm_model="chat_llm",
        sub_agents=[ "browser_agent"]
    )
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="查询一下东汉公元几几年灭亡的"
        )


if __name__ == "__main__":
    asyncio.run(main())
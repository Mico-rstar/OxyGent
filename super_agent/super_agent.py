import asyncio
import os
from dotenv import load_dotenv

from oxygent import MAS, Config, oxy, preset_tools
from tools.multimodal_tools import multimodal_tools
from tools.document_reader import document_tools
from prompts import BROWSER_SYSTEM_PROMPT, MASTER_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT, NAVIGATE_AGENT

# 自动加载 .env 文件中的环境变量
load_dotenv()

Config.set_agent_llm_model("default_llm")


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
    multimodal_tools,
    document_tools,
    preset_tools.math_tools,
    # oxy.StdioMCPClient(
    #     name="browser_tool",
    #     params={
    #         "command": "npx",
    #         "args": ["-y", "@midscene/mcp"],
    #         "env": {
    #             "MIDSCENE_MODEL_NAME": "REPLACE_WITH_YOUR_MODEL_NAME",
    #             "OPENAI_API_KEY": "REPLACE_WITH_YOUR_OPENAI_API_KEY",
    #             "MCP_SERVER_REQUEST_TIMEOUT": "800000"
    #         }
    #     },
    #     category="tool",
    #     class_name="StdioMCPClient",
    #     desc="Browser automation tools via MCP",
    #     desc_for_llm="Browser automation tools via MCP protocol"
    # ),
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
    # oxy.StdioMCPClient(
    #     name="bilibili_tool",
    #     params={
    #         "command": "uvx",
    #         "args": [
    #             "bilibili-video-info-mcp"
    #         ],
    #         "env": {
    #             "SESSDATA": "291a4d7f%2C1776822769%2Ccd1d4%2Aa2CjAxyNqdhhOz9-MzqX7A2f9mF8QzuIuunF847jM5c_YrvNuaddXj68U6vMsq7MtSfJwSVk9fME9TMFlFWVNHdmVCVHJEb1F1end3bzJYZXdaVjNLMnFQQWRfV2NXRTRoMXktdVhIUjAtcmVVblBHbi1taUxnS3p0dy1kSXRwQW1IQmxDWnhzMF9nIIEC"
    #         }
    #     },
    #     category="tool",
    #     class_name="StdioMCPClient",
    #     desc="Browser automation tools via MCP",
    #     desc_for_llm="通过MCP协议提取b站字幕、弹幕、评论"
    # ),

    oxy.ReActAgent(
            name="browser_agent",
            llm_model="chat_llm",
            desc="可以使用浏览器检索信息的agent",
            desc_for_llm="浏览器使用专家agent，请在query中描述具体任务",
            category="agent",
            class_name="ReActAgent",
            tools=["browser_tool"],
            # sub_agents=["browser_navigate_agent"],
            prompt=BROWSER_SYSTEM_PROMPT,
            is_entrance=False,
            is_permission_required=False,
            is_save_data=True,
            is_multimodal_supported=False,
            semaphore=2,

            short_memory_size=1,              # 减少到5轮对话
            memory_max_tokens=8000,           # 减少Token限制
            is_discard_react_memory=True,     # 丢弃详细ReAct记忆
            weight_short_memory=8,            # 增加短期记忆权重
            weight_react_memory=1,            # 降低ReAct记忆权重
            max_react_rounds=8,               # 减少最大推理轮数
        ),
    oxy.ReActAgent(
            name="math_agent",
            llm_model="chat_llm",
            desc="可以使用数学工具解决数学问题的agent",
            desc_for_llm="可以使用数学工具解决数学问题的agent",
            category="agent",
            tools=["math_tools"],
        ),
    oxy.ReActAgent(
            name="mutimodel_agent",
            llm_model="chat_llm",
            desc="可以理解图片，视频的多模态理解agent",
            desc_for_llm="可以理解图片，视频的多模态理解agent",
            category="agent",
            tools=["multimodal_tools"],
    ),
    oxy.ReActAgent(
            name="browser_navigate_agent",
            desc_for_llm="navigate到指定页面，并对页面内容进行压缩agent",
            category="agent",
            llm_model="flash_llm",
            prompt=NAVIGATE_AGENT,
            tools=["browser_tool"],

            short_memory_size=1,
            memory_max_tokens=8000,           # 减少Token限制
            is_discard_react_memory=True,     # 丢弃详细ReAct记忆
            weight_short_memory=8,            # 增加短期记忆权重
            weight_react_memory=1,            # 降低ReAct记忆权重
            max_react_rounds=8,               # 减少最大推理轮数
    ),
    oxy.ReActAgent(
        name="document_agent",
        llm_model="chat_llm",
        desc="可以读取txt,pdf,ppt,xlsx格式文件的agent",
        desc_for_llm="可以读取txt,pdf,ppt,xlsx格式文件的agent",
        category="agent",
        tools=["document_tools"],
    ),
    oxy.ReActAgent(
        name="executor_agent",
        prompt=EXECUTOR_SYSTEM_PROMPT,
        llm_model="chat_llm",
        sub_agents=["mutimodel_agent", "document_agent", "math_agent", "browser_agent"],
        # tools=["browser_tool", "bilibili_tool"],
    ),
    oxy.ReActAgent(
        is_master=True,
        name="master_agent",
        prompt=MASTER_SYSTEM_PROMPT,
        llm_model="chat_llm",
        sub_agents=[ "executor_agent"],
    ),
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="What time is it now? Please save it into time.txt."
        )


if __name__ == "__main__":
    asyncio.run(main())
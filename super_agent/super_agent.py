import asyncio
import os
from dotenv import load_dotenv

from oxygent import MAS, Config, oxy, preset_tools
from tools.multimodal_tools import multimodal_tools
from tools.document_reader import document_tools
from tools.stock_tools import stock_tools
from tools.python_tools import python_tools
from prompts import BROWSER_SYSTEM_PROMPT, MASTER_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT, PLANNER_SYSTEM_PROMPT, PAGE_CONTENT_COMPRESSION_PROMPT, BROWSER_TOOL_PROXY_DESC, STOCK_SYSTEM_PROMPT, PYTHON_SYSTEM_PROMPT
from workflow.workflows import data_workflow, planner_executor_workflow

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
    oxy.HttpLLM(
        name="coder_llm",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("CODER_LLM_MODEL_NAME"),
    ),
    multimodal_tools,
    document_tools,
    stock_tools,
    python_tools,
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
            desc_for_llm="浏览器使用专家agent,专门负责网页操作和信息检索,包括点击、导航、表单填写、页面截图理解等",
            category="agent",
            class_name="ReActAgent",
            # tools=["browser_tool", "stock_tools"],
            sub_agents=["browser_proxy_agent"],
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
            name="mutimodel_agent",
            llm_model="chat_llm",
            desc="可以理解图片，视频的多模态理解agent",
            desc_for_llm="可以理解图片，视频的多模态理解agent",
            category="agent",
            tools=["multimodal_tools"],
    ),
    oxy.ReActAgent(
            name="python_agent",
            llm_model="coder_llm",
            desc="Python代码专家，编写代码并运行得到结果，可以利用python进行操作系统交互，网络任务，算法执行，数据分析，逻辑验证，计算任务",
            desc_for_llm="Python代码专家，专门负责代码生成、执行和数据分析计算任务",
            prompt=PYTHON_SYSTEM_PROMPT,
            category="agent",
            tools=["python_tools"],
            # 能力边界：仅处理Python代码相关任务，不处理网页操作、文件读取、股票查询等
    ),
    # oxy.ReActAgent(
    #         name="browser_navigate_agent",
    #         desc_for_llm="navigate到指定页面，并对页面内容进行压缩agent",
    #         category="agent",
    #         llm_model="flash_llm",
    #         prompt=NAVIGATE_AGENT,
    #         tools=["browser_tool"],

    #         short_memory_size=1,
    #         memory_max_tokens=8000,           # 减少Token限制
    #         is_discard_react_memory=True,     # 丢弃详细ReAct记忆
    #         weight_short_memory=8,            # 增加短期记忆权重
    #         weight_react_memory=1,            # 降低ReAct记忆权重
    #         max_react_rounds=8,               # 减少最大推理轮数
    # ),
    oxy.ChatAgent(
        name='compress_agent',
        prompt=PAGE_CONTENT_COMPRESSION_PROMPT,
        llm_model='flash_llm',
        short_memory_size=1
    ),
    oxy.WorkflowAgent(
        name='browser_proxy_agent',
        desc=BROWSER_TOOL_PROXY_DESC,
        sub_agents=['compress_agent'],
        tools = ["browser_tool"],
        func_workflow=data_workflow,
        llm_model='flash_llm',
        is_retain_master_short_memory=True,
        extra_permitted_tool_name_list=["browser_tool"]
    ),
    oxy.ReActAgent(
        name="document_agent",
        llm_model="chat_llm",
        desc="文档处理专家，专门负责读取和解析txt、pdf、ppt、xlsx等多种格式文档",
        desc_for_llm="文档处理专家，专门负责读取和解析txt、pdf、ppt、xlsx等多种格式文档",
        # 能力边界：仅处理文档读取和内容提取任务，不处理网页操作、代码执行、股票查询等
        category="agent",
        tools=["document_tools"],
    ),
    # 规划智能体 - 内部使用，不对外暴露
    oxy.ReActAgent(
        name="planner_agent",
        prompt=PLANNER_SYSTEM_PROMPT,
        llm_model="chat_llm",
        desc="任务规划智能体，负责将复杂任务分解为可执行的计划",
        desc_for_llm="任务规划智能体，负责将复杂任务分解为可执行的计划",
        category="agent",
        is_entrance=False,
        is_permission_required=False,
        is_save_data=True,
        is_multimodal_supported=False,
        short_memory_size=3,
        memory_max_tokens=16000,
    ),

    # 股票智能体 - 专门负责股票数据查询
    oxy.ReActAgent(
        name="stock_agent",
        llm_model="chat_llm",
        desc="股票数据查询专家，专门负责港股和美股历史数据查询和分析",
        desc_for_llm="股票数据查询专家，专门负责港股和美股历史数据查询和分析",
        # 能力边界：仅处理股票数据查询任务，不处理网页操作、代码执行、文件读取等
        prompt=STOCK_SYSTEM_PROMPT,
        category="agent",
        tools=["stock_tools"],
    ),

    # 执行智能体 - 内部使用，不对外暴露
    oxy.ReActAgent(
        name="executor_agent",
        prompt=EXECUTOR_SYSTEM_PROMPT,
        llm_model="chat_llm",
        sub_agents=["mutimodel_agent", "document_agent", "browser_agent", "stock_agent", "python_agent"],
        # tools=["browser_tool", "bilibili_tool"],
    ),

    # 规划-执行工作流 - 封装planner和executor的主要工作流
    oxy.WorkflowAgent(
        name="planner_executor_workflow",
        desc="规划-执行工作流，负责将复杂任务先规划后执行",
        desc_for_llm="规划-执行工作流，负责将复杂任务先规划后执行",
        sub_agents=["planner_agent", "executor_agent"],
        func_workflow=planner_executor_workflow,
        llm_model="chat_llm",
        is_retain_master_short_memory=True,
        is_entrance=False,
        is_permission_required=False,
        is_save_data=True,
        is_multimodal_supported=False,
    ),

    # 主智能体 - 只负责调用工作流和输出结果
    oxy.ReActAgent(
        is_master=True,
        name="master_agent",
        prompt=MASTER_SYSTEM_PROMPT,
        llm_model="chat_llm",
        sub_agents=["planner_executor_workflow"],
    )
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="What time is it now? Please save it into time.txt."
        )


if __name__ == "__main__":
    asyncio.run(main())
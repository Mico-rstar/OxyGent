import asyncio
import os
from dotenv import load_dotenv

from oxygent import MAS, Config, oxy, OxyRequest
from prompts import BROWSER_TOOL_PROXY_DESC, BROWSER_SYSTEM_PROMPT, PAGE_CONTENT_COMPRESSION_PROMPT

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
        tool_name = query_data.get('tool')
        filter_question = query_data.get('filter_question')

        if not tool_name:
            return "错误：未指定浏览器操作工具"
        else:
            query_data.pop('tool', '')
            query_data.pop('filter_query', '')
        

        # 代理调用浏览器工具
        browser_response = await oxy_request.call(
            callee=tool_name,
            arguments=query_data
        )

        # 检查浏览器操作状态，如果不成功则重试一次
        max_browser_retries = 2
        browser_retry_count = 0

        while browser_response.state.name != "COMPLETED" and browser_retry_count < max_browser_retries:
            browser_retry_count += 1
            print(f"[Data Workflow] 浏览器操作失败: {browser_response.state.name}，进行第 {browser_retry_count} 次重试")

            browser_response = await oxy_request.call(
                callee=tool_name,
                arguments=query_data
            )

        # 如果重试后仍然失败，返回错误
        if browser_response.state.name != "COMPLETED":
            return f"浏览器操作失败，已重试 {max_browser_retries} 次: {browser_response.state.name}"

        
        # 检查是否需要进行页面压缩
        if (tool_name not in ['take_snapshot', 'press_key'] or
            not filter_question or
            len(filter_question.strip()) == 0):
            print("[Data Workflow] 无需页面压缩，直接返回浏览器结果")
            return browser_response.output

        # 进行页面压缩
        print(f"[Data Workflow] 开始页面压缩，过滤问题: {filter_question}")

        compress_response = await oxy_request.call(
            callee='compress_agent',
            arguments={
                "query": f"## 过滤问题: {filter_question} \n\n ## 页面内容: {browser_response.output}"
            }
        )

        if compress_response.state.name == "COMPLETED":
            return compress_response.output
        else:
            # 如果压缩失败，返回原始页面内容
            print("[Data Workflow] 压缩失败，返回原始页面内容")
            return browser_response.output


        


    except json.JSONDecodeError:
        return "错误：查询参数不是有效的JSON格式"
    except Exception as e:
        return f"执行浏览器操作时发生错误: {str(e)}"





# async def main():
#     async with MAS(oxy_space=oxy_space) as mas:
#         await mas.start_web_service(
#             first_query="查询一下东汉公元几几年灭亡的"
#         )


if __name__ == "__main__":
    # asyncio.run(main())
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
    oxy.ChatAgent(
        name='compress_agent',
        prompt=PAGE_CONTENT_COMPRESSION_PROMPT,
        llm_model='flash_llm',
        short_memory_size=1
    ),
    oxy.WorkflowAgent(
        name='browser_agent',
        desc=BROWSER_TOOL_PROXY_DESC,
        sub_agents=['compress_agent'],
        tools = ["browser_tool"],
        func_workflow=data_workflow,
        llm_model='flash_llm',
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
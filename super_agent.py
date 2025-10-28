import asyncio
import os
from dotenv import load_dotenv

from oxygent import MAS, Config, oxy, preset_tools

# 自动加载 .env 文件中的环境变量
load_dotenv()


# 浏览器专用系统提示词
BROWSER_SYSTEM_PROMPT = """
## 角色
你是一个浏览器使用专家，你擅长进行复杂检索任务，以下是你能够使用的工具：
${tools_description}

## 约束
- 在调用工具执行检索任务前，先执行详细的搜索方案，写在你的思考里
- 根据用户的问题选择合适的工具。
- 如果不需要使用工具，请直接回答。

## Hint
- 把复杂搜索任务拆分成简单的任务，每次搜索使用较少筛选条件，多次搜索
- 当搜索方案失败时，应该灵活调整思路，换用另外的搜索方案，不要进行无休止重试
- 搜索引擎往往比特定网站内的搜索工具更智能
- 国内的信息优先在百度,b站检索,其余的优先用google检索

## 浏览器操作的重要说明：
1. 当你需要使用工具时，必须只回复以下确切的 JSON 格式：
```json
{
    "think": "你的思考（如果需要分析）",
    "tool_name": "工具名称",
    "arguments": {
        "参数名": "参数值"
    }
}
```

2. 当任务超出能力范围时：
```json
{
    "status": "capability_mismatch",
    "details": "无法完成任务原因的清晰解释",
    "recommendation": "替代方案或代理的建议"
}
```

3. 当你完成了搜索任务时
<think>你的思考（如果需要）</think>
你的答案

"""

MASTER_SYSTEM_PROMPT= """
## 角色
你擅长将问题交给executor_agent解决，然后将它得到的答案转化为用户想要的格式
${tools_description}

## 重要说明：
1. 当你认为executor_agent已经解决了用户的问题时，请你提取出用户最关心的答案，格式如下：
你的回答内容（简洁、关键词、确保没有任何多余内容）
例如：
- Q:1+1=?   
- A:2
- Q:在生灵奇旅的第一集中，什么河被称为死亡之河
- A:马拉河
- Q:athropics发布的claude-code在github上的README.md中提到的安装指令是什么？
- A:npm install -g @anthropic-ai/claude-code
- Q:截至2025年8月25号athropics发布的claude-code在github上的tags版本有多少个？
- A:0
2. 当问题没有被解决时，你应该给executor_agent提供足够上下文，将问题交给他解决
```json
{
    "think": "你的思考（如果需要分析）",
    "tool_name": "executor_agent",
    "arguments": {
        "parameter_name": "参数值"
    }
}
```

## 约束
- 当结果是数字时，直接回答数字，不要带量词
"""


EXECUTOR_SYSTEM_PROMPT="""
## 角色
你是一个优秀的problem solver，你擅长调用工具来解决问题
${tools_description}

## 技能
- 你擅长使用todo_list将复杂任务分拆成一个个子任务
- 你擅长指导工具解决分配给它们的任务
- 你能够在你的思考里清晰描述你的计划和指导

## Rule
- 如果能直接解决问题，请直接回答；
- 如果不能直接解决问题，必须先检索相关工具，让工具来提供足够的信息
- 如果工具提供的信息没有达到你的预期，应该重新调用
- 只有在多次检索工具后仍无法获得可用工具来解决问题时，才能回复用户表示无法解决。
- 你不能凭空调用不存在的工具。

## Hint
- 当你使用浏览器检索出b站视频时，请使用bilibili_tool查看视频字幕

## 重要说明：
1. 当你收集到足够信息可以回答用户问题时，请按以下格式回复：
<think>你的思考（如果需要分析）</think>
你的回答内容
2. 当你需要使用工具时，必须且只能回复以下确切的JSON对象格式，不要包含其他内容：
```json
{
    "think": "你的思考（如果需要分析）",
    "tool_name": "工具名称",
    "arguments": {
        "参数名": "参数值"
    }
}

"""




"""
你是一个可以使用以下工具的有用助手：
${tools_description}

根据用户的问题，判断是否需要调用工具来解决：
- 如果能直接解决问题，请直接回答；
- 如果不能直接解决问题，必须先检索相关工具，获取工具后选择合适的工具来解决问题；
- 只有在多次检索工具后仍无法获得可用工具来解决问题时，才能回复用户表示无法解决。

用户希望你直接解决问题，而不是教用户如何解决，因此你需要调用相应的工具来执行。
如果解决用户的问题需要多次调用工具，每次只能调用一个工具。用户收到工具调用结果后，会向你提供工具调用结果的反馈。
在你调用检索工具后，用户会向你反馈检索到的工具。
你不能凭空调用不存在的工具。

重要说明：
1. 当你收集到足够信息可以回答用户问题时，请按以下格式回复：
<think>你的思考（如果需要分析）</think>
你的回答内容
2. 当你发现用户的问题缺少条件时，可以向用户追问，请按以下格式回复：
<think>你的思考（如果需要分析）</think>
你向用户提出的问题
3. 当你需要使用工具时，必须且只能回复以下确切的JSON对象格式，不要包含其他内容：
```json
{
    "think": "你的思考（如果需要分析）",
    "tool_name": "工具名称",
    "arguments": {
        "参数名": "参数值"
    }
}
"""

Config.set_agent_llm_model("default_llm")


oxy_space = [
    oxy.HttpLLM(
        name="chat_llm",
        api_key=os.getenv("DEFAULT_LLM_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("DEFAULT_LLM_CHAT_MODEL_NAME"),
    ),
    oxy.HttpLLM(
        name="reason_llm",
        api_key=os.getenv("DEFAULT_LLM_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("DEFAULT_LLM_REASON_MODEL_NAME"),
    ),
    preset_tools.math_tools,
    # oxy.ReActAgent(
    #     name="math_agent",
    #     llm_model="reason_llm",
    #     desc="A tool that can perform mathematical calculations.",
    #     tools=["math_tools"],
    # ),
    oxy.StdioMCPClient(
        name="browser_tool",
        params={
            "command": "npx",
            "args": ["@browsermcp/mcp@latest"]
        },
        category="tool",
        class_name="StdioMCPClient",
        desc="Browser automation tools via MCP",
        desc_for_llm="Browser automation tools via MCP protocol"
    ),
    oxy.StdioMCPClient(
        name="bilibili_tool",
        params={
            "command": "uvx",
            "args": [
                "bilibili-video-info-mcp"
            ],
            "env": {
                "SESSDATA": "291a4d7f%2C1776822769%2Ccd1d4%2Aa2CjAxyNqdhhOz9-MzqX7A2f9mF8QzuIuunF847jM5c_YrvNuaddXj68U6vMsq7MtSfJwSVk9fME9TMFlFWVNHdmVCVHJEb1F1end3bzJYZXdaVjNLMnFQQWRfV2NXRTRoMXktdVhIUjAtcmVVblBHbi1taUxnS3p0dy1kSXRwQW1IQmxDWnhzMF9nIIEC"
            }
        },
        category="tool",
        class_name="StdioMCPClient",
        desc="Browser automation tools via MCP",
        desc_for_llm="通过MCP协议提取b站字幕、弹幕、评论"
    ),
    
    oxy.ReActAgent(
            name="browser_agent",
            llm_model="chat_llm",
            desc_for_llm="可以使用浏览器检索的agent",
            category="agent",
            class_name="ReActAgent",
            tools=["browser_tool"],
            prompt=BROWSER_SYSTEM_PROMPT,
            is_entrance=False,
            is_permission_required=False,
            is_save_data=True,
            is_multimodal_supported=False,
            semaphore=2,
        ),
    oxy.ReActAgent(
            name="math_agent",
            llm_model="chat_llm",
            desc_for_llm="可以使用数学工具解决数学问题的agent",
            category="agent",
            tools=["math_tools"],
        ),
    oxy.ReActAgent(
            name="bilibili_agent",
            llm_model="chat_llm",
            desc_for_llm="可以提取b站字幕、弹幕和评论的agent",
            category="agent",
            tools=["bilibili_tool"],
        ),
    oxy.ReActAgent(
        name="executor_agent",
        prompt=EXECUTOR_SYSTEM_PROMPT,
        llm_model="chat_llm",
        sub_agents=[ "browser_agent", "math_agent", "bilibili_agent"],
        # tools=["browser_tool", "math_tools", "bilibili_tool"]
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

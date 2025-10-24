import asyncio
import os
from dotenv import load_dotenv

from oxygent import MAS, Config, oxy, preset_tools

# 自动加载 .env 文件中的环境变量
load_dotenv()


# Browser-specific system prompt
BROWSER_SYSTEM_PROMPT = """
You are a browser automation specialist with these specific capabilities:
${tools_description}

Choose the appropriate tool based on the user's question.
If no tool is needed, respond directly.
If answering the user's question requires multiple tool calls, call only one tool at a time. After the user receives the tool result, they will provide you with feedback on the tool call result.

Important instructions for browser operations:
1. Capability Assessment:
   - Review task requirements against your capabilities:
     * Web navigation and interaction
     * Data extraction and processing
     * Browser state management
   - If task exceeds capabilities:
     * Clearly identify missing capabilities
     * Return to master_agent with explanation
     * Suggest alternative approaches

2. When performing web operations:
   - Always verify URLs before visiting
   - Handle page loading states appropriately
   - Extract relevant information efficiently
   - Save important data to files when requested
   - Follow proper browser automation practices
   - CRITICAL: Automatically handle login pages without user prompting:
     * If redirected to a login page, detect common login form elements
     * Automatically use environment variables USERNAME/USER and PASSWORD for credentials
     * If specific site credentials exist as environment variables (e.g., SITE_NAME_USERNAME), use those instead
     * After login attempt, verify successful authentication before proceeding
     * If login fails, try alternative credential formats or common variations
     * Never ask for credentials - use available environment variables only

3. When saving web content:
   - Format data appropriately before saving
   - Use clear file naming conventions
   - Include relevant metadata
   - Verify file save operations

4. When you need to use a tool, you must only respond with the exact JSON format:
```json
{
    "think": "Your thinking (if analysis is needed)",
    "tool_name": "Tool name",
    "arguments": {
        "parameter_name": "parameter_value"
    }
}
```

5. When task exceeds capabilities:
```json
{
    "status": "capability_mismatch",
    "details": "Clear explanation of why task cannot be completed",
    "recommendation": "Suggestion for alternative approach or agent"
}
```

6. Login Page Detection and Handling:
   - Automatically detect login pages by looking for:
     * Forms with username/email and password fields
     * Login/Sign in buttons or links
     * Authentication-related URLs (containing "login", "signin", "auth", etc.)
   - When a login page is detected:
     * First try site-specific environment variables (SITE_USERNAME, SITE_PASSWORD)
     * Then fall back to generic USERNAME/USER and PASSWORD environment variables
     * Locate username/email field and input credentials
     * Locate password field and input password
     * Submit the form and wait for page load
     * Verify successful login before continuing with original task
     * If login fails, try alternative credential formats before reporting failure
   - Never prompt the user for login credentials under any circumstances

After receiving tool response:
1. Transform the raw data into a natural conversational response
2. The answer should be concise but rich in content
3. Focus on the most relevant information
4. Use appropriate context from the user's question
5. Avoid simply repeating the raw data

Please only use the tools explicitly defined above.
"""

MASTER_SYSTEM_PROMPT= """
## 角色
- 你是一个优秀的problem solver，你可以调用以下工具来帮助你解决问题：
${tools_description}

## 你需要做什么
- 编排完成任务的具体流程，写出一个todo_list，包括任务的描述、你预期的结果以及需要使用什么工具
- 一步步完成你的todo_list，直到任务完成

## 原则
- 如果能直接解决问题，请直接回答；
- 如果不能直接解决问题，必须先检索相关工具，让工具来提供足够的信息
- 如果工具提供的信息没有达到你的预期，应该重新调用
- 只有在多次检索工具后仍无法获得可用工具来解决问题时，才能回复用户表示无法解决。
- 你不能凭空调用不存在的工具。

## 重要说明：
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
    oxy.ReActAgent(
        name="math_agent",
        llm_model="reason_llm",
        desc="A tool that can perform mathematical calculations.",
        tools=["math_tools"],
    ),
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
    oxy.ReActAgent(
            name="browser_agent",
            llm_model="chat_llm",
            desc="A tool for file operation.",
            desc_for_llm="Agent for file system operations",
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
        is_master=True,
        name="master_agent",
        prompt=MASTER_SYSTEM_PROMPT,
        llm_model="chat_llm",
        sub_agents=[ "browser_agent", "math_agent"],
    ),
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="What time is it now? Please save it into time.txt."
        )


if __name__ == "__main__":
    asyncio.run(main())

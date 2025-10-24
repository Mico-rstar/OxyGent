import asyncio
import os
from dotenv import load_dotenv

from oxygent import MAS, Config, oxy, preset_tools

# 自动加载 .env 文件中的环境变量
load_dotenv()


# 浏览器专用系统提示词
BROWSER_SYSTEM_PROMPT = """
你是一个浏览器自动化专家，具备以下特定能力：
${tools_description}

根据用户的问题选择合适的工具。
如果不需要使用工具，请直接回答。
如果回答用户问题需要多次调用工具，每次只能调用一个工具。用户收到工具结果后，会向你提供工具调用结果的反馈。

浏览器操作的重要说明：
1. 能力评估：
   - 对照任务需求评估你的能力：
     * 网页导航和交互
     * 数据提取和处理
     * 浏览器状态管理
   - 如果任务超出能力范围：
     * 明确识别缺失的能力
     * 向 master_agent 返回并解释
     * 建议替代方案

2. 执行网页操作时：
   - 访问前始终验证 URL
   - 适当处理页面加载状态
   - 高效提取相关信息
   - 根据请求将重要数据保存到文件
   - 遵循正确的浏览器自动化实践
   - 关键：自动处理登录页面，无需用户提示：
     * 如果重定向到登录页面，检测常见登录表单元素
     * 自动使用环境变量 USERNAME/USER 和 PASSWORD 作为凭据
     * 如果存在站点特定的环境变量凭据（如 SITE_NAME_USERNAME），优先使用
     * 登录尝试后，在继续前验证成功认证
     * 如果登录失败，尝试其他凭据格式或常见变体
     * 绝不索要凭据 - 仅使用可用的环境变量

3. 保存网页内容时：
   - 保存前适当格式化数据
   - 使用清晰的文件命名约定
   - 包含相关元数据
   - 验证文件保存操作

4. 当你需要使用工具时，必须只回复以下确切的 JSON 格式：
```json
{
    "think": "你的思考（如果需要分析）",
    "tool_name": "工具名称",
    "arguments": {
        "参数名": "参数值"
    }
}
```

5. 当任务超出能力范围时：
```json
{
    "status": "capability_mismatch",
    "details": "无法完成任务原因的清晰解释",
    "recommendation": "替代方案或代理的建议"
}
```

6. 登录页面检测和处理：
   - 通过查找以下内容自动检测登录页面：
     * 包含用户名/邮箱和密码字段的表单
     * 登录/登录按钮或链接
     * 认证相关 URL（包含 "login", "signin", "auth" 等）
   - 当检测到登录页面时：
     * 首先尝试站点特定的环境变量（SITE_USERNAME, SITE_PASSWORD）
     * 然后回退到通用的 USERNAME/USER 和 PASSWORD 环境变量
     * 定位用户名/邮箱字段并输入凭据
     * 定位密码字段并输入密码
     * 提交表单并等待页面加载
     * 在继续原始任务前验证成功登录
     * 如果登录失败，在报告失败前尝试其他凭据格式
   - 在任何情况下都不要提示用户提供登录凭据

收到工具响应后：
1. 将原始数据转换为自然的对话回复
2. 回答应简洁但内容丰富
3. 专注于最相关的信息
4. 使用用户问题的适当上下文
5. 避免简单重复原始数据

请仅使用上面明确定义的工具。
"""

MASTER_SYSTEM_PROMPT= """
## 角色
你是一个优秀的problem solver，你擅长编排任务流程以及调用工具来解决复杂问题
${tools_description}

## 你需要做什么
- 编排完成任务的具体流程，写出一个todo_list
- 一步步完成你的todo_list，直到任务完成

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
你的回答内容（简洁、关键词、确保没有任何多余内容）
例如：
- Q:1+1=?   
- A:2
- Q:在生灵奇旅的第一集中，什么河被称为死亡之河
- A:马拉河
- Q:athropics发布的claude-code在github上的README.md中提到的安装指令是什么？
- A:npm install -g @anthropic-ai/claude-code
- Q:截至2025年8月25号athropics发布的claude-code在github上的tags版本有多少个？
- A:<think>我没有看到任何tags版本，用户问有几个，我应该直接回答0</think>0

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
    
    # oxy.ReActAgent(
    #         name="browser_agent",
    #         llm_model="chat_llm",
    #         desc="A tool for file operation.",
    #         desc_for_llm="Agent for file system operations",
    #         category="agent",
    #         class_name="ReActAgent",
    #         tools=["browser_tool"],
    #         prompt=BROWSER_SYSTEM_PROMPT,
    #         is_entrance=False,
    #         is_permission_required=False,
    #         is_save_data=True,
    #         is_multimodal_supported=False,
    #         semaphore=2,
    #     ),
    oxy.ReActAgent(
        is_master=True,
        name="master_agent",
        prompt=MASTER_SYSTEM_PROMPT,
        llm_model="chat_llm",
        # sub_agents=[ "browser_agent", "math_agent"],
        tools=["browser_tool", "math_tools", "bilibili_tool"]
    ),
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="What time is it now? Please save it into time.txt."
        )


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
多模态工具使用示例
演示如何在OxyGent框架中使用多模态理解工具
"""

import asyncio
import os
from pydantic import Field

from oxygent import MAS, oxy
from multimodal_tools import multimodal_tools

# 配置LLM
oxy_space = [
    oxy.HttpLLM(
        name="default_llm",
        api_key=os.getenv("DEFAULT_LLM_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("DEFAULT_LLM_MODEL_NAME"),
    ),
    multimodal_tools,
    oxy.ReActAgent(
        name="multimodal_agent",
        tools=["multimodal_tools"],
        llm_model="default_llm",
    ),
]


async def main():
    """主函数 - 启动多模态智能体"""
    print("启动多模态理解智能体...")
    print("可用功能:")
    print("- 图片内容理解")
    print("- 视频内容理解")
    print("- 多模态配置检查")
    print("\n您可以询问:")
    print("- '请分析这张图片: /path/to/image.jpg'")
    print("- '这段视频讲了什么: /path/to/video.mp4'")
    print("- '检查多模态工具的配置状态'")

    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(first_query="你好！我是一个多模态理解助手，可以帮你分析图片和视频内容。请提供图片或视频文件的路径，我来为你分析。")


if __name__ == "__main__":
    # 检查必要的环境变量
    required_env_vars = [
        "DASHSCOPE_API_KEY",  # 阿里云DashScope API Key
        "DEFAULT_LLM_API_KEY",
        "DEFAULT_LLM_BASE_URL",
        "DEFAULT_LLM_MODEL_NAME"
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print("缺少必要的环境变量:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n请设置环境变量后重新运行")
        print("例如:")
        print("export DASHSCOPE_API_KEY='your-dashscope-api-key'")
        print("export DEFAULT_LLM_API_KEY='your-llm-api-key'")
        print("export DEFAULT_LLM_BASE_URL='your-llm-base-url'")
        print("export DEFAULT_LLM_MODEL_NAME='your-llm-model-name'")
    else:
        asyncio.run(main())
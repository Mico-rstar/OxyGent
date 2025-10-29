"""
多模态理解工具 - 支持图片和视频理解
基于阿里云通义千问多模态模型
"""

import os
from typing import Optional
from pydantic import Field

try:
    from dashscope import MultiModalConversation
    import dashscope
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

from oxygent.oxy import FunctionHub

multimodal_tools = FunctionHub(name="multimodal_tools")


@multimodal_tools.tool(description="理解图片内容并提供详细描述")
def understand_image(
    image_path: str = Field(description="图片文件的绝对路径"),
    question: str = Field(default="请描述这张图片的内容", description="关于图片的问题，默认为描述图片内容"),
) -> str:
    """
    使用阿里云通义千问多模态模型理解图片内容

    Args:
        image_path: 图片文件的绝对路径
        question: 关于图片的问题
        api_key: 阿里云DashScope API Key
        model: 模型名称

    Returns:
        图片理解结果的文本描述

    Raises:
        ImportError: 如果dashscope库未安装
        FileNotFoundError: 如果图片文件不存在
        ValueError: 如果API调用失败
    """
    model: str = "qwen3-vl-plus"
    if not DASHSCOPE_AVAILABLE:
        raise ImportError("dashscope库未安装，请使用 'pip install dashscope' 安装")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    # 使用提供的API Key或环境变量
    key = os.getenv('DASHSCOPE_API_KEY')
    if not key:
        raise ValueError("未找到DashScope API Key，请设置环境变量DASHSCOPE_API_KEY或提供api_key参数")

    try:
        # 构建图片路径
        image_uri = f"file://{image_path}"

        # 构建消息
        messages = [
            {
                'role': 'user',
                'content': [
                    {'image': image_uri},
                    {'text': question}
                ]
            }
        ]

        # 调用API
        response = MultiModalConversation.call(
            api_key=key,
            model=model,
            messages=messages
        )

        # 检查响应状态
        if response.status_code != 200:
            raise ValueError(f"API调用失败，状态码: {response.status_code}, 响应: {response.message}")

        # 提取结果
        result = response["output"]["choices"][0]["message"]["content"][0]["text"]
        return result

    except Exception as e:
        raise ValueError(f"图片理解失败: {str(e)}")


@multimodal_tools.tool(description="理解视频内容并提供详细描述")
def understand_video(
    video_path: str = Field(description="视频文件的路径"),
    question: str = Field(default="请描述这段视频的内容", description="关于视频的问题，默认为描述视频内容"),
) -> str:
    """
    使用阿里云通义千问多模态模型理解视频内容

    Args:
        video_path: 视频文件的绝对路径
        question: 关于视频的问题
        fps: 视频抽帧帧率，控制抽取帧的数量
        api_key: 阿里云DashScope API Key
        model: 模型名称
        use_intl: 是否使用新加坡地域的API

    Returns:
        视频理解结果的文本描述

    Raises:
        ImportError: 如果dashscope库未安装
        FileNotFoundError: 如果视频文件不存在
        ValueError: 如果API调用失败
    """
    model: str = "qwen3-vl-plus"
    fps: float = 2.0
    if not DASHSCOPE_AVAILABLE:
        raise ImportError("dashscope库未安装，请使用 'pip install dashscope' 安装")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    # 使用提供的API Key或环境变量
    key = os.getenv('DASHSCOPE_API_KEY')
    if not key:
        raise ValueError("未找到DashScope API Key，请设置环境变量DASHSCOPE_API_KEY或提供api_key参数")

    try:

        # 构建视频路径
        video_uri = f"file://{video_path}"

        # 构建消息
        messages = [
            {
                'role': 'user',
                'content': [
                    {'video': video_uri, "fps": fps},
                    {'text': question}
                ]
            }
        ]

        # 调用API
        response = MultiModalConversation.call(
            api_key=key,
            model=model,
            messages=messages
        )

        # 检查响应状态
        if response.status_code != 200:
            raise ValueError(f"API调用失败，状态码: {response.status_code}, 响应: {response.message}")

        # 提取结果
        result = response["output"]["choices"][0]["message"]["content"][0]["text"]
        return result

    except Exception as e:
        raise ValueError(f"视频理解失败: {str(e)}")


@multimodal_tools.tool(description="检查多模态工具的依赖和配置")
def check_multimodal_setup() -> dict:
    """
    检查多模态工具的依赖和配置状态

    Returns:
        包含检查结果的字典
    """
    result = {
        "dashscope_installed": DASHSCOPE_AVAILABLE,
        "api_key_configured": bool(os.getenv('DASHSCOPE_API_KEY')),
        "supported_models": ["qwen3-vl-plus", "qwen3-vl-max", "qwen-vl-plus", "qwen-vl-max"],
        "recommended_model": "qwen3-vl-plus"
    }

    if not DASHSCOPE_AVAILABLE:
        result["install_command"] = "pip install dashscope"
        result["status"] = "error"
        result["message"] = "dashscope库未安装"
    elif not result["api_key_configured"]:
        result["status"] = "error"
        result["message"] = "未配置DashScope API Key"
    else:
        result["status"] = "ready"
        result["message"] = "多模态工具配置完成，可以使用"

    return result
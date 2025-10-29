#!/usr/bin/env python3
"""
多模态工具测试脚本
"""

import asyncio
import os
import sys

# 添加父目录到路径以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multimodal_tools import check_multimodal_setup


async def test_setup():
    """测试多模态工具的配置状态"""
    print("=== 多模态工具配置检查 ===")

    result = await check_multimodal_setup()

    print(f"DashScope库安装状态: {'✓' if result['dashscope_installed'] else '✗'}")
    print(f"API Key配置状态: {'✓' if result['api_key_configured'] else '✗'}")
    print(f"支持的模型: {', '.join(result['supported_models'])}")
    print(f"推荐模型: {result['recommended_model']}")
    print(f"整体状态: {result['status']}")
    print(f"消息: {result['message']}")

    if not result['dashscope_installed']:
        print(f"\n安装命令: {result.get('install_command', 'N/A')}")

    return result['status'] == 'ready'


def test_image_understanding():
    """测试图片理解功能（需要实际的图片文件）"""
    print("\n=== 图片理解功能测试 ===")

    # 检查是否有测试图片
    test_image_path = "/tmp/test_image.jpg"  # 用户需要提供实际的图片路径

    if not os.path.exists(test_image_path):
        print(f"测试图片不存在: {test_image_path}")
        print("请将测试图片放在指定路径或修改test_image_path变量")
        return False

    try:
        from multimodal_tools import understand_image

        result = understand_image(
            image_path=test_image_path,
            question="请描述这张图片的主要内容"
        )

        print("图片理解结果:")
        print(result)
        return True

    except Exception as e:
        print(f"图片理解测试失败: {str(e)}")
        return False


def test_video_understanding():
    """测试视频理解功能（需要实际的视频文件）"""
    print("\n=== 视频理解功能测试 ===")

    # 检查是否有测试视频
    test_video_path = "/tmp/test_video.mp4"  # 用户需要提供实际的视频路径

    if not os.path.exists(test_video_path):
        print(f"测试视频不存在: {test_video_path}")
        print("请将测试视频放在指定路径或修改test_video_path变量")
        return False

    try:
        from multimodal_tools import understand_video

        result = understand_video(
            video_path=test_video_path,
            question="请描述这段视频的主要内容",
            fps=1.0  # 降低抽帧频率以节省API调用
        )

        print("视频理解结果:")
        print(result)
        return True

    except Exception as e:
        print(f"视频理解测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("多模态工具测试开始...\n")

    # 测试配置
    setup_ok = await test_setup()

    if not setup_ok:
        print("\n配置检查失败，请先解决依赖和配置问题")
        return

    # 询问用户是否要测试实际功能
    print("\n配置检查通过！")

    # 注意：实际的图片和视频测试需要用户提供文件
    print("\n要进行完整的功能测试，请：")
    print("1. 准备测试图片文件")
    print("2. 准备测试视频文件")
    print("3. 修改test_image_path和test_video_path变量")
    print("4. 重新运行测试脚本")

    # 可选：取消注释下面的代码来测试实际功能
    # test_image_understanding()
    # test_video_understanding()

    print("\n多模态工具测试完成")


if __name__ == "__main__":
    asyncio.run(main())
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union

from oxygent.oxy import FunctionHub

logger = logging.getLogger(__name__)
python_tools = FunctionHub(name="python_tools")


def get_working_directory() -> str:
    """
    从环境变量获取Python子进程的工作目录

    Returns:
        工作目录路径，如果未配置则返回当前工作目录
    """
    # 优先从环境变量获取
    work_dir = os.getenv('PYTHON_WORK_DIR')

    if work_dir and os.path.exists(work_dir):
        logger.info(f"Using configured working directory: {work_dir}")
        return work_dir
    elif work_dir:
        logger.warning(f"Configured working directory does not exist: {work_dir}, creating it")
        os.makedirs(work_dir, exist_ok=True)
        return work_dir
    else:
        # 默认使用当前工作目录
        default_dir = os.getcwd()
        logger.info(f"No working directory configured, using current directory: {default_dir}")
        return default_dir


@python_tools.tool(
    description="在子进程中运行Python代码并返回执行结果，完全隔离环境"
)
def run_python_code(
    code: str,
    variable_to_return: Optional[str] = None,
    timeout: int = 30,
    python_executable: Optional[str] = None
) -> str:
    """
    在子进程中运行Python代码并返回执行结果，完全隔离环境

    Args:
        code: 要执行的Python代码
        variable_to_return: 要返回的变量名（可选）
        timeout: 超时时间（秒），默认30秒
        python_executable: Python可执行文件路径，默认使用当前Python解释器

    Returns:
        执行结果，包含标准输出和标准错误输出
    """
    # 确定Python可执行文件路径
    if python_executable is None:
        python_executable = sys.executable

    try:
        # 获取工作目录
        work_dir = get_working_directory()
        logger.info(f"Running Python code in subprocess with timeout: {timeout}s, working directory: {work_dir}")

        # 如果需要返回特定变量，构建包装代码
        if variable_to_return:
            wrapped_code = f"""
{code}

if '{variable_to_return}' in locals():
    import json
    print(json.dumps({{ 'variable': repr({variable_to_return}) }}))
else:
    print(f"Error: Variable '{variable_to_return}' not found")
"""
        else:
            wrapped_code = code

        # 创建子进程运行Python代码
        result = subprocess.run(
            [python_executable, "-c", wrapped_code],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=work_dir
        )

        # 处理输出
        if result.returncode == 0:
            output = result.stdout.strip()

            # 如果指定了要返回的变量，尝试解析JSON输出
            if variable_to_return and output:
                try:
                    import json
                    json_output = json.loads(output)
                    return f"Variable '{variable_to_return}': {json_output['variable']}"
                except json.JSONDecodeError:
                    return f"Output:\n{output}"
            else:
                return f"Output:\n{output}" if output else "Code executed successfully (no output)"
        else:
            error_msg = f"Error:\n{result.stderr.strip()}" if result.stderr.strip() else "Unknown error occurred"
            logger.error(f"Python code execution failed: {error_msg}")
            return error_msg

    except subprocess.TimeoutExpired:
        error_msg = f"Python code execution timed out after {timeout} seconds"
        logger.error(error_msg)
        return error_msg

    except Exception as e:
        error_msg = f"Error running Python code: {str(e)}"
        logger.error(error_msg)
        return error_msg


@python_tools.tool(
    description="安装Python依赖库"
)
def pip_install(library_name: str, python_executable: Optional[str] = None) -> str:
    """
    安装指定的Python库

    Args:
        library_name: 要安装的库名称
        python_executable: Python可执行文件路径，默认使用当前Python解释器

    Returns:
        安装结果信息
    """
    # 确定Python可执行文件路径
    if python_executable is None:
        python_executable = sys.executable

    try:
        # 获取工作目录
        work_dir = get_working_directory()
        logger.info(f"Installing library: {library_name}, working directory: {work_dir}")

        # 使用subprocess运行pip install命令
        result = subprocess.run(
            [python_executable, "-m", "pip", "install", library_name],
            capture_output=True,
            text=True,
            timeout=300,  # 5分钟超时
            cwd=work_dir
        )

        if result.returncode == 0:
            logger.info(f"Successfully installed {library_name}")
            return f"Successfully installed {library_name}\nOutput: {result.stdout}"
        else:
            logger.error(f"Failed to install {library_name}: {result.stderr}")
            return f"Failed to install {library_name}\nError: {result.stderr}"

    except subprocess.TimeoutExpired:
        error_msg = f"Installation of {library_name} timed out after 5 minutes"
        logger.error(error_msg)
        return error_msg

    except Exception as e:
        error_msg = f"Error installing {library_name}: {str(e)}"
        logger.error(error_msg)
        return error_msg


# @python_tools.tool(
#     description="在当前环境运行pip uninstall"
# )
# def pip_uninstall(library_name: str) -> str:
#     """
#     卸载指定的Python库

#     Args:
#         library_name: 要卸载的库名称

#     Returns:
#         卸载结果信息
#     """
#     try:
#         logger.info(f"Uninstalling library: {library_name}")

#         # 使用subprocess运行pip uninstall命令，添加-y参数自动确认卸载
#         result = subprocess.run(
#             [sys.executable, "-m", "pip", "uninstall", "-y", library_name],
#             capture_output=True,
#             text=True,
#             timeout=180  # 3分钟超时
#         )

#         if result.returncode == 0:
#             logger.info(f"Successfully uninstalled {library_name}")
#             return f"Successfully uninstalled {library_name}\nOutput: {result.stdout}"
#         else:
#             logger.error(f"Failed to uninstall {library_name}: {result.stderr}")
#             return f"Failed to uninstall {library_name}\nError: {result.stderr}"

#     except subprocess.TimeoutExpired:
#         error_msg = f"Uninstallation of {library_name} timed out after 3 minutes"
#         logger.error(error_msg)
#         return error_msg

#     except Exception as e:
#         error_msg = f"Error uninstalling {library_name}: {str(e)}"
#         logger.error(error_msg)
#         return error_msg
import asyncio
import os
import json
import ast
from datetime import datetime
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

def build_query(query, filename):
    """
    构建查询字符串，如果file_name不为空，则在query前加上file_path前缀

    Args:
        query (str): 原始查询字符串
        file_name (str, optional): 文件名，如果为None或空字符串，则不加前缀
        file_path (str): 文件路径前缀，默认为"FILE_PATH"

    Returns:
        str: 构建后的查询字符串
    """
    if filename and len(filename.strip()) > 0:
        return f"filename:{filename.strip()} + \n\n + {query.strip()}"
    else:
        return query.strip()


def load_test_data(data_path):
    """加载测试数据"""
    test_data = []
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    test_data.append(json.loads(line))
        print(f"成功加载 {len(test_data)} 条测试数据")
        return test_data
    except Exception as e:
        print(f"加载数据失败: {e}")
        return []



async def main():
    # 设置实验名称用于结果保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    Config.set_app_name(f'mas_test_{timestamp}')

    # 加载验证集数据（也可以改为测试集）
    data_path = os.path.join(os.getenv('DEFAULT_FILE_PATH'), 'to_do.jsonl')
    # 如果要使用测试集，请取消注释下面一行并注释上面一行
    # data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'test', 'data.jsonl')

    test_data = load_test_data(data_path)
    if not test_data:
        print("没有找到测试数据，退出程序")
        return

    print(f"开始处理 {len(test_data)} 个任务...")
    print("选择处理模式:")
    print("1. 串行处理 (推荐用于调试)")
    print("2. 批量处理 (推荐用于高效运行)")

    # 这里可以设置为 True 来使用批量处理
    use_batch_processing = True  # 设为 True 启用批量处理

    results = []

    async with MAS(oxy_space=oxy_space) as mas:
        # 先启动Web服务以确保MCP正确初始化
        # if use_batch_processing:
        # 批量处理模式 - 每次5个任务
        print("使用批量处理模式（每次处理1个任务）...")

        batch_size = 1
        total_tasks = len(test_data)

        for batch_start in range(0, total_tasks, batch_size):
            batch_end = min(batch_start + batch_size, total_tasks)
            batch_tasks = test_data[batch_start:batch_end]

            print(f"\n处理批次 {batch_start//batch_size + 1}: 任务 {batch_start+1}-{batch_end}")

            # 构建当前批次的查询列表，如果file_name不为空则加上前缀
            batch_queries = [build_query(task['query'], task.get('file_name', '')) for task in batch_tasks]
            batch_results = await mas.start_batch_processing(batch_queries, return_trace_id=True)

            for i, (task_data, result) in enumerate(zip(batch_tasks, batch_results)):
                # 提取结果
                answer = ""
                # 直接处理字典类型的结果
                if isinstance(result, dict):
                    if 'output' in result:
                        answer = str(result['output'])
                    else:
                        answer = str(result)
                elif isinstance(result, str):
                    # 如果结果字符串看起来像字典，尝试解析
                    try:
                        parsed_result = ast.literal_eval(result)
                        if isinstance(parsed_result, dict) and 'output' in parsed_result:
                            answer = str(parsed_result['output'])
                        else:
                            answer = result
                    except:
                        answer = result
                elif hasattr(result, 'output'):
                    answer = str(result.output)
                elif hasattr(result, 'answer'):
                    answer = str(result.answer)
                else:
                    answer = str(result)

                results.append({
                    "task_id": task_data['task_id'],
                    "answer": answer.strip(),
                    "original_query": task_data['query'],
                    "level": task_data.get('level', ''),
                    "file_name": task_data.get('file_name', ''),
                    "true_answer": task_data.get('answer', ''),
                    "steps": task_data.get('steps', '')
                })

                print(f"任务 {task_data['task_id']} 完成，答案: {answer[:100]}...")
                # 每个批次完成后保存中间结果
                current_progress = batch_end
                save_results(results, os.getenv('DEFAULT_FILE_PATH') + f"test_results\\intermediate_results_{current_progress}.jsonl")
                print(f"已保存中间结果 ({current_progress}/{total_tasks} 个任务)")

            
                # 显示进度
                progress_percentage = (current_progress / total_tasks) * 100
                print(f"总体进度: {progress_percentage:.1f}% ({current_progress}/{total_tasks})")
        # else:
        #     # 串行处理模式 - 便于调试和监控
        #     print("使用串行处理模式...")
        #     for i, task_data in enumerate(test_data, 1):
        #         print(f"\n进度: {i}/{len(test_data)}")
        #         await process_single_task(mas, task_data, results)

        #         # 每10个任务保存一次中间结果
        #         if i % 10 == 0:
        #             save_results(results, f"intermediate_results_{i}.jsonl")
        #             print(f"已保存中间结果 ({i} 个任务)")

    # 保存最终结果
    final_result_file = f"./test_results/final_results_{timestamp}.jsonl"
    save_results(results, final_result_file)

    # 生成简化格式的结果文件（用于提交）
    submission_file = f"./test_results/submission_results_{timestamp}.jsonl"
    save_submission_format(results, submission_file)

    print(f"\n所有任务处理完成！")
    print(f"详细结果保存在: {final_result_file}")
    print(f"提交格式结果保存在: {submission_file}")

    # 统计信息
    total_tasks = len(results)
    successful_tasks = len([r for r in results if not r['answer'].startswith('ERROR')])
    error_tasks = total_tasks - successful_tasks

    print(f"\n统计信息:")
    print(f"总任务数: {total_tasks}")
    print(f"成功任务数: {successful_tasks}")
    print(f"失败任务数: {error_tasks}")
    print(f"成功率: {successful_tasks/total_tasks*100:.2f}%")

    # 如果有验证集答案，计算准确率
    if test_data and 'answer' in test_data[0]:
        correct_tasks = 0
        for result in results:
            if not result['answer'].startswith('ERROR') and result['answer'] == result['true_answer']:
                correct_tasks += 1

        print(f"验证集准确率: {correct_tasks/total_tasks*100:.2f}% ({correct_tasks}/{total_tasks})")


def save_results(results, filename):
    """保存详细结果"""
    with open(filename, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')


def save_submission_format(results, filename):
    """保存提交格式的结果（仅task_id和answer）"""
    with open(filename, 'w', encoding='utf-8') as f:
        for result in results:
            submission_data = {
                "task_id": result["task_id"],
                "answer": result["answer"]
            }
            f.write(json.dumps(submission_data, ensure_ascii=False) + '\n')


if __name__ == "__main__":
    asyncio.run(main())
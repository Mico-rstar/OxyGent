import os
import dashscope
from dotenv import load_dotenv

load_dotenv()


# 若使用新加坡地域的模型，请释放下列注释
# dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

PROMPT_TICKET_EXTRACTION = """
将图片信息转为markdown文本,
"""

image_dir='/home/rene/projs/super-agent/OxyGent/super_agent/tools/test_files/test.png'

try:
    response = dashscope.MultiModalConversation.call(
        model='qwen-vl-ocr-latest',
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        messages=[{
            'role': 'user',
            'content': [
                {'image': f'file://{image_dir}'},
                # qwen-vl-ocr、qwen-vl-ocr-latest、qwen-vl-ocr-2025-04-13及以后的快照模型未设置内置任务时，支持在以下text字段中传入Prompt，若未传入则使用默认的Prompt：Please output only the text content from the image without any additional descriptions or formatting.
                # 如调用qwen-vl-ocr-1028，模型会使用固定Prompt：Read all the text in the image.，不支持用户在text中传入自定义Prompt
                {'text': PROMPT_TICKET_EXTRACTION}
            ]
        }]
    )
    print(response.output.choices[0].message.content[0]['text'])
except Exception as e:
    print(f"An error occurred: {e}")
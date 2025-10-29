### 图片理解模型调用
```python
import os
from dashscope import MultiModalConversation
import dashscope 

# 将xxx/eagle.png替换为你本地图像的绝对路径
local_path = "xxx/eagle.png"
image_path = f"file://{local_path}"
messages = [
                {'role':'user',
                'content': [{'image': image_path},
                            {'text': '图中描绘的是什么景象?'}]}]
response = MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    model='qwen3-vl-plus',  # 此处以qwen3-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
    messages=messages)
print(response["output"]["choices"][0]["message"].content[0]["text"])
```



### 视频理解模型调用
```python
import os
from dashscope import MultiModalConversation
import dashscope 

# 若使用新加坡地域的模型，请取消下列注释
# dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

# 将xxxx/test.mp4替换为你本地视频的绝对路径
local_path = "xxx/test.mp4"
video_path = f"file://{local_path}"
messages = [
                {'role':'user',
                # fps参数控制视频抽帧数量，表示每隔1/fps 秒抽取一帧
                'content': [{'video': video_path,"fps":2},
                            {'text': '这段视频描绘的是什么景象?'}]}]
response = MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    model='qwen3-vl-plus',  
    messages=messages)
print(response["output"]["choices"][0]["message"].content[0]["text"])
```


### ocr
```python
import os
import dashscope

# 若使用新加坡地域的模型，请释放下列注释
# dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

PROMPT_TICKET_EXTRACTION = """
请提取车票图像中的发票号码、车次、起始站、终点站、发车日期和时间点、座位号、席别类型、票价、身份证号码、购票人姓名。
要求准确无误的提取上述关键信息、不要遗漏和捏造虚假信息，模糊或者强光遮挡的单个文字可以用英文问号?代替。
返回数据格式以json方式输出，格式为：{'发票号码'：'xxx', '车次'：'xxx', '起始站'：'xxx', '终点站'：'xxx', '发车日期和时间点'：'xxx', '座位号'：'xxx', '席别类型'：'xxx','票价':'xxx', '身份证号码'：'xxx', '购票人姓名'：'xxx'"},
"""

try:
    response = dashscope.MultiModalConversation.call(
        model='qwen-vl-ocr-latest',
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key=os.getenv('DASHSCOPE_API_KEY'),
        messages=[{
            'role': 'user',
            'content': [
                {'image': 'https://img.alicdn.com/imgextra/i2/O1CN01ktT8451iQutqReELT_!!6000000004408-0-tps-689-487.jpg'},
                # qwen-vl-ocr、qwen-vl-ocr-latest、qwen-vl-ocr-2025-04-13及以后的快照模型未设置内置任务时，支持在以下text字段中传入Prompt，若未传入则使用默认的Prompt：Please output only the text content from the image without any additional descriptions or formatting.
                # 如调用qwen-vl-ocr-1028，模型会使用固定Prompt：Read all the text in the image.，不支持用户在text中传入自定义Prompt
                {'text': PROMPT_TICKET_EXTRACTION}
            ]
        }]
    )
    print(response.output.choices[0].message.content[0]['text'])
except Exception as e:
    print(f"An error occurred: {e}")
```

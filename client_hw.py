import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

huawei_api_key = os.getenv("HUAWEI_API_KEY")


def get_model_response(system_content, user_content):
    url = "https://api.modelarts-maas.com/v1/chat/completions"
    api_key = huawei_api_key  # 请替换为你的API密钥

    # 设置请求头
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # 准备请求数据
    data = {
        "model": "DeepSeek-V3",  # 模型名称
        "messages": [
            {"role": "system", "content": system_content},  # 系统角色内容
            {"role": "user", "content": user_content},  # 用户角色内容
        ],
        "stream": False,  # 是否开启流式推理
        "temperature": 0.6,  # 采样随机性控制
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    # 返回模型的回答
    if response.status_code == 200:
        result = response.json()  # 将返回的JSON数据转换为字典
        return result["choices"][0]["message"]["content"]  # 提取模型回答的内容
    else:
        print(f"Error: {response.status_code}")
        return None


# 示例用法
if __name__ == "__main__":
    system_content = "你是一个有用的软件工程课程助手。"  # 系统角色内容
    user_content = "你好"  # 用户角色内容

    response = get_model_response(system_content, user_content)
    print(response)

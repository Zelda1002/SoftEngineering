import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

HUAWEI_API_KEY = os.getenv("HUAWEI_API_KEY")


def get_model_response(system_content, user_content):
    """调用华为云API获取模型回应"""
    url = "https://api.modelarts-maas.com/v1/chat/completions"
    api_key = HUAWEI_API_KEY

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    data = {
        "model": "DeepSeek-V3",
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "temperature": 0.6,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        print(f"Error: {response.status_code}")
        return None


def code_to_flowchart(code, language="python"):
    """
    将代码发送给DeepSeek模型，生成对应的Graphviz格式流程图

    参数:
        code (str): 要分析的代码
        language (str): 代码的编程语言，默认为'python'

    返回:
        str: 生成的Graphviz DOT格式的流程图代码
    """
    system_content = """
    你是一位专业的代码分析专家，精通将代码转换成清晰的Graphviz流程图。
    请分析提供的代码，并创建一个Graphviz DOT格式的流程图，展示程序的执行流程和逻辑结构。

    注意事项:
    1. 只输出Graphviz DOT格式的代码，不要有其他解释
    2. 使用digraph结构，适当的节点和边表示代码逻辑
    3. 为节点添加合适的标签，清晰描述代码功能
    4. 包含条件分支、循环结构等关键控制流程
    5. 使用有层次的排版和合适的颜色，提高可读性
    6. DOT代码必须是有效的，可以直接用Graphviz工具渲染
    """

    user_content = f"""
    请将以下{language}代码转换为Graphviz流程图:

    ```{language}
    {code}
    ```

    只返回完整的DOT格式代码，不要包含其他解释或markdown标记。
    """

    response = get_model_response(system_content, user_content)
    graphviz_code = extract_graphviz_code(response)
    return graphviz_code


def extract_graphviz_code(response):
    """
    从模型回复中提取Graphviz DOT代码

    参数:
        response (str): 模型的回复内容

    返回:
        str: 提取的Graphviz DOT代码
    """
    if "```dot" in response or "```graphviz" in response:
        start_markers = ["```dot", "```graphviz"]
        end_marker = "```"

        for marker in start_markers:
            if marker in response:
                start_idx = response.find(marker) + len(marker)
                end_idx = response.find(end_marker, start_idx)
                if end_idx != -1:
                    return response[start_idx:end_idx].strip()

    if "digraph" in response:
        start_idx = response.find("digraph")
        end_idx = response.rfind("}")
        if end_idx != -1 and end_idx > start_idx:
            return response[start_idx : end_idx + 1].strip()

    return response.strip()


def save_graphviz_to_file(graphviz_code, output_file="flowchart.dot"):
    """
    将Graphviz代码保存到文件

    参数:
        graphviz_code (str): Graphviz DOT格式代码
        output_file (str): 输出文件路径
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(graphviz_code)
    return output_file


def render_graphviz(graphviz_code, output_format="png", output_file="flowchart.png"):
    """
    渲染Graphviz代码为图像

    参数:
        graphviz_code (str): Graphviz DOT格式代码
        output_format (str): 输出格式，如'png', 'svg'等
        output_file (str): 输出文件路径

    返回:
        tuple: (是否成功, 输出文件路径或错误信息)
    """
    try:
        # 创建输出目录（如果不存在）
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 使用绝对路径创建临时文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        temp_file = os.path.join(current_dir, "temp_flowchart.dot")

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(graphviz_code)

        # 使用绝对路径进行渲染
        abs_output_file = os.path.abspath(output_file)

        # 尝试使用不同的Graphviz命令
        commands = [
            f'dot -T{output_format} "{temp_file}" -o "{abs_output_file}"',
            f'graphviz -T{output_format} "{temp_file}" -o "{abs_output_file}"',
        ]

        success = False
        for cmd in commands:
            result = os.system(cmd)
            if result == 0:
                success = True
                break

        if not success:
            # 如果系统命令失败，尝试使用Python的graphviz库
            try:
                import graphviz

                source = graphviz.Source(graphviz_code)
                source.render(
                    abs_output_file.replace(f".{output_format}", ""),
                    format=output_format,
                    cleanup=True,
                )
                success = True
            except ImportError:
                return (
                    False,
                    "Graphviz渲染失败。请安装Graphviz软件或Python graphviz库：pip install graphviz",
                )
            except Exception as e:
                return False, f"使用Python graphviz库渲染失败: {str(e)}"

        # 检查文件是否成功创建
        if not os.path.exists(abs_output_file):
            return False, f"无法找到生成的图像文件: {abs_output_file}"

        # 删除临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)

        return True, abs_output_file

    except Exception as e:
        return False, f"渲染图像时发生错误: {str(e)}"


def generate_flowchart_from_code(code, language="python"):
    """
    完整的代码转流程图流程，返回结果供Gradio使用

    参数:
        code (str): 要分析的代码
        language (str): 代码的编程语言

    返回:
        tuple: (graphviz_code, image_path, success_message)
    """
    if not code.strip():
        return "", None, "请输入要分析的代码"

    if not HUAWEI_API_KEY:
        return "", None, "错误：未配置HUAWEI_API_KEY环境变量"

    try:
        # 生成Graphviz代码
        graphviz_code = code_to_flowchart(code, language)

        if not graphviz_code:
            return "", None, "生成流程图失败，请稍后重试"

        # 创建输出目录 - 使用新的static/flowcharts目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "static", "flowcharts")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 生成唯一的文件名
        timestamp = int(time.time())
        output_file = os.path.join(output_dir, f"flowchart_{timestamp}.png")

        # 渲染图像
        success, result = render_graphviz(
            graphviz_code, output_format="png", output_file=output_file
        )

        if success:
            return (
                graphviz_code,
                result,
                f"流程图生成成功！图像已保存至: {os.path.basename(result)}",
            )
        else:
            # 如果渲染失败，至少保存DOT文件
            dot_file = os.path.join(output_dir, f"flowchart_{timestamp}.dot")
            save_graphviz_to_file(graphviz_code, dot_file)
            return (
                graphviz_code,
                None,
                f"Graphviz渲染失败，但DOT代码已保存。错误信息: {result}",
            )

    except Exception as e:
        return "", None, f"生成流程图时发生错误: {str(e)}"


def create_download_link(file_path):
    """
    为生成的文件创建下载链接

    参数:
        file_path (str): 文件路径

    返回:
        str: 文件路径，用于Gradio下载
    """
    if file_path and os.path.exists(file_path):
        return file_path
    return None

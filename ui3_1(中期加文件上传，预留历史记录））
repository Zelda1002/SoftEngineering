import gradio as gr
import os
import re
from agents import AgentManager, AGENT_CLASSES  # 导入你的智能体管理器和类定义
from flowchart_generator import generate_flowchart_from_code  # 导入流程图生成功能

import json
import textract, mimetypes
from PIL import Image
import pytesseract

# 创建智能体管理器实例
agent_manager = AgentManager()
# 一次最多生成题目数
qcountmax = 5

# 动态生成历史文件路径
def get_history_file(bot_type):
    return f"chat_history_{bot_type}.json"

def load_history(bot_type):
    history_file = get_history_file(bot_type)
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(history, bot_type):
    history_file = get_history_file(bot_type)
    with open(history_file, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=4)

def view_history(bot_type):
    history = load_history(bot_type)
    formatted_history = "\n".join(
        f"{item['role']}: {item['content']}" for item in history
    )
    # 调试信息
    print(f"历史记录内容: {formatted_history}")
    return gr.update(value=formatted_history, visible=True)

def close_history():
    return gr.update(visible=False)

# 聊天回应逻辑
def chatbot_response(user_message, bot_type, history):
    try:
        # 确保针对当前智能体的历史记录
        if not isinstance(history, dict):
            history = {}
        if bot_type not in history:
            history[bot_type] = []  # 初始化当前智能体的历史记录

        agent = agent_manager.get_agent(bot_type)
        if agent:
            response = agent.process(user_message)
        else:
            response = f"没有找到名为 {bot_type} 的智能体。"
    except Exception as e:
        response = f"发生错误：{str(e)}"

    history[bot_type].append({"role": "user", "content": user_message})
    history[bot_type].append({"role": "assistant", "content": response})
    save_history(history[bot_type], bot_type)
    return history[bot_type], history


# 章节选择RAG聊天回应逻辑
def chapter_rag_response(user_message, bot_type, selected_chapter, history):
    agent = agent_manager.get_agent(bot_type)
    if agent:
        response = agent.process(user_message, selected_chapter)
    else:
        response = f"没有找到名为 {bot_type} 的智能体。"
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response})
    return history, history


# 解析文件的函数（根据文件类型使用textract和OCR进行解析）
def parse_file(file_obj):
    fname = file_obj.name
    ext = os.path.splitext(fname)[-1].lower()

    if ext in [".docx", ".pdf"]:
        text = textract.process(fname).decode("utf-8")
        return text.strip()

    if ext in [".png", ".jpg", ".jpeg"]:
        img = Image.open(fname)
        text = pytesseract.image_to_string(img, lang="eng+chi_sim")
        return text.strip()

    raise ValueError("暂不支持该文件类型")



# HTML 内容列表（功能2,4,5）
html_contents = """
    <h2>思维导图</h2>
    <iframe src="http://119.3.225.124:50/swdt0.html" style="width:100%; height:calc(100vh - 80px); border:none;"></iframe>
    """

# 自定义样式
css = """
    body, html {
        margin: 0; padding: 0; height: 100%;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        background-color: #fffef5;
        color: #4b4500;
        user-select: none;
        zoom: 1.1;
    }
    #sidebar {
        background-color: #fff9e6;
        height: 100vh;
        padding: 30px 20px;
        box-sizing: border-box;
        border-right: 1.5px solid #e6d9a6;
        display: flex;
        flex-direction: column;
        align-items: stretch;
        box-shadow: 2px 0 8px rgb(230 210 160 / 0.3);
    }
    #sidebar h2 {
        color: #6b5700;
        margin: 0 0 40px 0;
        font-weight: 900;
        font-size: 28px;
        letter-spacing: 1.5px;
    }
    #sidebar button {
        width: 100%;
        margin-bottom: 16px;
        background-color: #fff9e6;
        border: 2px solid #d9c770;
        color: #6b5700;
        font-weight: 700;
        padding: 14px 0;
        cursor: pointer;
        border-radius: 8px;
        font-size: 17px;
        transition: background-color 0.25s, box-shadow 0.25s;
        box-shadow: inset 0 0 0 0 transparent;
    }
    #sidebar button:hover {
        background-color: #f4e9b4;
        box-shadow: inset 0 0 10px 2px #f4e9b4;
    }
    #sidebar button:focus {
        outline: none;
        border-color: #a38c00;
        box-shadow: 0 0 8px 3px #d9c770;
    }
    #content {
        padding: 40px 35px;
        background-color: #fffef5;
        height: 100vh;
        overflow-y: auto;
        box-sizing: border-box;
        font-size: 18px;
        line-height: 1.6;
        color: #3f3a00;
        user-select: text;
    }
    #input-row {
        display: flex;
        align-items: center;
        margin-top: 16px;
    }
    #input-row textarea {
        flex: 1;
        resize: none;
        height: 60px;
        font-size: 16px;
        padding: 10px;
        border: 2px solid #d9c770;
        border-radius: 8px;
        background-color: #fffef5;
        color: #3f3a00;
        box-sizing: border-box;
    }
    #input-row button {
        margin-left: 10px;
        padding: 14px 20px;
        font-size: 16px;
        font-weight: bold;
        background-color: #fff9e6;
        border: 2px solid #d9c770;
        border-radius: 8px;
        color: #6b5700;
        cursor: pointer;
        transition: background-color 0.25s, box-shadow 0.25s;
    }
    #input-row button:hover {
        background-color: #f4e9b4;
        box-shadow: inset 0 0 10px 2px #f4e9b4;
    }
"""

# 构建主界面
with gr.Blocks(css=css) as demo:
    with gr.Row():
        #左侧功能按键栏
        with gr.Column(elem_id="sidebar", scale=1, min_width=200):

            # 👉 包一层 Column，确保结构整齐
            with gr.Column():
                gr.Markdown("<h2>软件工程课程助手</h2>", elem_id="sidebar_title")
                names = ["💬智能问答", "🧠思维导图", "🔥章节问答", "🧭画流程图", "📅题目练习"]
                btns = [gr.Button(names[i], elem_id=f"btn_{i}") for i in range(5)]
                file_upload = gr.File(label="选择docx、pdf、png、jpg、jpeg文件上传",
                                      file_types=[".docx", ".pdf", ".png", ".jpg", ".jpeg"])
                upload_btn = gr.Button("📤上传习题")

        #右侧显示页面
        with gr.Column(elem_id="content", scale=5) as content_area:
            # 功能1：聊天模块
            with gr.Column(visible=True) as chat_area:
                gr.Markdown("<h2 style='color:#6b5700;'>功能1: 智能对话</h2>")
                bot_dropdown = gr.Dropdown(
                    choices=list(AGENT_CLASSES.keys()),
                    label="选择机器人",
                    value="概念解释智能体",
                )
                chat_display = gr.Chatbot(type="messages", height=500)
                with gr.Row(elem_id="input-row"):
                    user_input = gr.Textbox(
                        placeholder="输入你的问题...",
                        show_label=False,
                        lines=2,
                        scale=8,
                    )
                    send_button = gr.Button("发送", scale=2)

                history = gr.State({})

                send_button.click(
                    chatbot_response,
                    inputs=[user_input, bot_dropdown, history],
                    outputs=[chat_display, history],
                )
                send_button.click(lambda: "", None, user_input)

            # 功能3：章节选择RAG模块
            with gr.Column(visible=False) as chapter_rag_area:
                gr.Markdown("<h2 style='color:#6b5700;'>章节问答</h2>")
                chapter_dropdown = gr.Dropdown(
                    choices=[
                        "全部章节",
                        "第一章：软件工程学概述",
                        "第二章：可行性研究",
                        "第三章：需求分析",
                        "第四章：形式化说明技术",
                        "第五章：总体设计",
                        "第六章：详细设计",
                        "第七章：实现",
                        "第八章：维护",
                        "第九章：面向对象方法学引论",
                        "第十章：面向对象分析",
                        "第十一章：面向对象设计",
                        "第十二章：面向对象实现",
                        "第十三章：软件项目管理",
                    ],
                    label="选择章节",
                    value="全部章节",
                )
                chapter_bot_dropdown = gr.Dropdown(
                    choices=list(AGENT_CLASSES.keys()),
                    label="选择机器人",
                    value="概念解释智能体",
                )
                chapter_chat_display = gr.Chatbot(type="messages", height=500)
                with gr.Row(elem_id="input-row"):
                    chapter_user_input = gr.Textbox(
                        placeholder="输入你的问题...",
                        show_label=False,
                        lines=2,
                        scale=8,
                    )
                    chapter_send_button = gr.Button("发送", scale=2)

                chapter_history = gr.State({})

                chapter_send_button.click(
                    chapter_rag_response,
                    inputs=[
                        chapter_user_input,
                        chapter_bot_dropdown,
                        chapter_dropdown,
                        chapter_history,
                    ],
                    outputs=[chapter_chat_display, chapter_history],
                )
                chapter_send_button.click(
                    lambda: "", None, chapter_user_input
                )
            # 功能4：代码流程图生成模块
            with gr.Column(visible=False) as flowchart_area:
                gr.Markdown("<h2 style='color:#6b5700;'>代码流程图生成</h2>")

                with gr.Row():
                    language_dropdown = gr.Dropdown(
                        choices=["python", "java", "javascript", "c", "cpp", "other"],
                        label="选择编程语言",
                        value="python",
                        scale=1,
                    )

                code_input = gr.Textbox(
                    placeholder="在这里输入你的代码...",
                    label="输入代码",
                    lines=10,
                    max_lines=20,
                )

                with gr.Row():
                    generate_btn = gr.Button("生成流程图", variant="primary", scale=2)
                    clear_btn = gr.Button("清空代码", scale=1)

                # 输出区域
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Graphviz DOT 代码")
                        dot_output = gr.Textbox(
                            label="生成的DOT代码",
                            lines=10,
                            max_lines=15,
                            interactive=False,
                        )
                        # DOT代码下载按钮
                        download_dot_btn = gr.DownloadButton(
                            label="下载DOT文件", visible=False
                        )

                    with gr.Column(scale=1):
                        gr.Markdown("### 流程图图像")
                        image_output = gr.Image(
                            label="生成的流程图", type="filepath", height=400
                        )
                        # 图片下载按钮
                        download_img_btn = gr.DownloadButton(
                            label="下载流程图图片", visible=False
                        )

                status_output = gr.Textbox(
                    label="状态信息",
                    lines=2,
                    interactive=False,
                )


                # 处理生成流程图的函数
                def handle_generate_flowchart(code, language):
                    dot_code, img_path, status = generate_flowchart_from_code(
                        code, language
                    )

                    # 创建临时DOT文件用于下载
                    dot_file_path = None
                    if dot_code:
                        import tempfile
                        import time

                        timestamp = int(time.time())
                        dot_file_path = f"./static/flowcharts/flowchart_{timestamp}.dot"

                        # 确保目录存在
                        os.makedirs(os.path.dirname(dot_file_path), exist_ok=True)

                        with open(dot_file_path, "w", encoding="utf-8") as f:
                            f.write(dot_code)

                    # 根据是否有结果显示下载按钮
                    dot_btn_visible = bool(dot_code)
                    img_btn_visible = bool(
                        img_path and os.path.exists(img_path) if img_path else False
                    )

                    return (
                        dot_code,
                        img_path,
                        status,
                        gr.update(
                            visible=dot_btn_visible,
                            value=dot_file_path if dot_btn_visible else None,
                        ),
                        gr.update(
                            visible=img_btn_visible,
                            value=img_path if img_btn_visible else None,
                        ),
                    )


                # 绑定事件
                generate_btn.click(
                    handle_generate_flowchart,
                    inputs=[code_input, language_dropdown],
                    outputs=[
                        dot_output,
                        image_output,
                        status_output,
                        download_dot_btn,
                        download_img_btn,
                    ],
                )

                clear_btn.click(
                    lambda: (
                        "",
                        "",
                        None,
                        "",
                        gr.update(visible=False),
                        gr.update(visible=False),
                    ),
                    outputs=[
                        code_input,
                        dot_output,
                        image_output,
                        status_output,
                        download_dot_btn,
                        download_img_btn,
                    ],
                )

            #功能五：智能出题
            with gr.Column(visible=False) as exercise_area:
                gr.Markdown("<h2 style='color:#6b5700;'>智能出题</h2>")

                # 第一排：章节 + 知识点
                with gr.Row():
                    exercise_chapter = gr.Dropdown(
                        label="选择章节",
                        choices=[
                            "第一章：软件工程学概述",
                            "第二章：可行性研究",
                            "第三章：需求分析",
                            "第四章：形式化说明技术",
                            "第五章：总体设计",
                            "第六章：详细设计",
                            "第七章：实现",
                            "第八章：维护",
                            "第九章：面向对象方法学引论",
                            "第十章：面向对象分析",
                            "第十一章：面向对象设计",
                            "第十二章：面向对象实现",
                            "第十三章：软件项目管理",
                        ],
                        value="综合各章",
                        interactive=True,
                        scale=1
                    )
                    exercise_topic = gr.Textbox(label="输入知识点（如：用例建模）", scale=1)

                # 第二排：难度 + 题型 + 数量
                with gr.Row():
                    exercise_difficulty = gr.Dropdown(
                        label="选择难度",
                        choices=["简单", "中等", "困难"],
                        value="中等",
                        scale=1
                    )
                    exercise_type = gr.Dropdown(
                        label="选择题型",
                        choices=["选择题", "填空题", "判断题", "简答题", "大题"],
                        value="选择题",
                        scale=1
                    )
                    exercise_count = gr.Slider(
                        label="题目数量",
                        minimum=1,
                        maximum=qcountmax,
                        step=1,
                        value=1,
                        interactive=True,
                        scale=1
                    )

                generate_button = gr.Button("🎯 生成题目")

                # 新增一个组件区域用于展示题目与答案卡片
                exercise_cards = gr.Column(visible=True)

                # 题目显示区：最多支持qcountmax道题
                exercise_blocks = []

                status_text = gr.Markdown("", visible=False)
                for i in range(qcountmax):
                    with gr.Column(visible=False) as blk:  # 默认都隐藏，生成时再显示
                        q_box = gr.Markdown("", visible=False)
                        with gr.Row():
                            ans_show_btn = gr.Button("👁️ 查看答案", visible=True, elem_id=f"ans_show_btn_{i}")
                            ans_hide_btn = gr.Button("❌ 隐藏答案", visible=False, elem_id=f"ans_hide_btn_{i}")
                        ans_box = gr.Markdown("", visible=False)

                        with gr.Row():
                            exp_show_btn = gr.Button("📖 查看解析", visible=True, elem_id=f"exp_show_btn_{i}")
                            exp_hide_btn = gr.Button("❌ 隐藏解析", visible=False, elem_id=f"exp_hide_btn_{i}")
                        exp_box = gr.Markdown("", visible=False)

                        exercise_blocks.append({
                            "q": q_box,
                            "ans_show_btn": ans_show_btn,
                            "ans_hide_btn": ans_hide_btn,
                            "a_box": ans_box,
                            "exp_show_btn": exp_show_btn,
                            "exp_hide_btn": exp_hide_btn,
                            "e_box": exp_box,
                            "column": blk,
                        })

            html_display = gr.HTML(visible=False)


        def split_result(result):
            # 使用正则分段
            parts = re.split(r"【题目】|【答案】|【解析】", result)
            if len(parts) >= 4:
                # parts[0] 是空白
                return parts[1].strip(), parts[2].strip(), parts[3].strip()
            else:
                return result.strip(), "未提供答案", "未提供解析"


        def generate_exercise(chapter, topic, difficulty, count, qtype):
            agent = agent_manager.get_agent("出题智能体")
            updates = []

            for i in range(qcountmax):
                if i < int(count):
                    print("调用出题：", chapter, topic, difficulty, count)
                    result = agent.process("请出一道题", selected_chapter=chapter, selected_topic=topic,
                                           difficulty=difficulty, question_type=qtype)
                    print("返回结果：", result)

                    # 拆分题干、答案、解析
                    question, answer, explanation = split_result(result)

                    # 每一题的组件更新（全部显示，且 value 不为空）
                    updates += [
                        gr.update(value=f"### 📝 题目{i + 1}\n\n{question.strip()}", visible=True),  # 题目
                        gr.update(visible=True),  # 查看答案按钮显示
                        gr.update(visible=False),  # 隐藏答案按钮隐藏
                        gr.update(value=f"答案：\n{answer.strip()}", visible=False),
                        # gr.update(visible=False, value=f"**答案：**\n\n{answer.strip()}"),  # 答案区隐藏

                        gr.update(visible=True),  # 查看解析按钮显示
                        gr.update(visible=False),  # 隐藏解析按钮隐藏
                        gr.update(value=f"解析：\n{explanation.strip()}", visible=False),
                        # gr.update(visible=False, value=f"**解析：**\n\n{explanation.strip()}"),  # 解析区隐藏

                        gr.update(visible=True),  # 整个卡片显示
                    ]

                else:
                    # 剩下的题目卡片全部隐藏
                    updates += [gr.update(visible=False)] * 8

            return updates


        def on_generate_start():
            return gr.update(value="⌛ 正在生成中，请稍候...", visible=True)


        generate_button.click(
            fn=on_generate_start,
            inputs=[],
            outputs=status_text
        ).then(
            fn=generate_exercise,
            inputs=[exercise_chapter, exercise_topic, exercise_difficulty, exercise_count, exercise_type],
            outputs=[
                *([item for blk in exercise_blocks for item in (
                    blk["q"],
                    blk["ans_show_btn"],
                    blk["ans_hide_btn"],
                    blk["a_box"],
                    blk["exp_show_btn"],
                    blk["exp_hide_btn"],
                    blk["e_box"],
                    blk["column"]
                )])
            ]
        ).then(
            fn=lambda: gr.update(value="✅ 题目已生成，请查看下方内容。", visible=True),
            outputs=status_text
        )

        # 为每个按钮手动绑定 click 行为（延迟绑定）
        for blk in exercise_blocks:
            # 查看答案按钮点击，直接显示答案，切换按钮显示状态
            blk["ans_show_btn"].click(
                lambda: (
                    gr.update(visible=True),  # 答案显示
                    gr.update(visible=False),  # 查看答案按钮隐藏
                    gr.update(visible=True)  # 隐藏答案按钮显示
                ),
                inputs=[],
                outputs=[blk["a_box"], blk["ans_show_btn"], blk["ans_hide_btn"]]
            )
            # 隐藏答案按钮点击，隐藏答案，切换按钮显示状态
            blk["ans_hide_btn"].click(
                lambda: (
                    gr.update(visible=False),  # 答案隐藏
                    gr.update(visible=True),  # 查看答案按钮显示
                    gr.update(visible=False)  # 隐藏答案按钮隐藏
                ),
                inputs=[],
                outputs=[blk["a_box"], blk["ans_show_btn"], blk["ans_hide_btn"]]
            )

            # 查看解析按钮点击，直接显示解析，切换按钮显示状态
            blk["exp_show_btn"].click(
                lambda: (
                    gr.update(visible=True),  # 解析显示
                    gr.update(visible=False),  # 查看解析按钮隐藏
                    gr.update(visible=True)  # 隐藏解析按钮显示
                ),
                inputs=[],
                outputs=[blk["e_box"], blk["exp_show_btn"], blk["exp_hide_btn"]]
            )
            # 隐藏解析按钮点击，隐藏解析，切换按钮显示状态
            blk["exp_hide_btn"].click(
                lambda: (
                    gr.update(visible=False),  # 解析隐藏
                    gr.update(visible=True),  # 查看解析按钮显示
                    gr.update(visible=False)  # 隐藏解析按钮隐藏
                ),
                inputs=[],
                outputs=[blk["e_box"], blk["exp_show_btn"], blk["exp_hide_btn"]]
            )


    def toggle_view(idx):
        if idx == 0:  # 功能1 - 智能问答
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                ""
            )
        elif idx == 1:  # 功能2 - 思维导图（显示 HTML）
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(value=html_contents)
            )
        elif idx == 2:  # 功能3 - 章节问答
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                ""
            )
        elif idx == 3:  # 功能4 - 代码流程图
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                ""
            )
        elif idx == 4:  # 功能5 - 智能出题（显示 exercise_area）
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),  # <== 这一项激活出题功能区
                gr.update(visible=False),
                ""
            )
        else:
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                ""
            )


    # 为每个按钮绑定点击事件
    for i, btn in enumerate(btns):
        btn.click(
            fn=lambda i=i: toggle_view(i),
            inputs=[],
            outputs=[
                chat_area,
                chapter_rag_area,
                flowchart_area,
                exercise_area,
                html_display,  # ✅ 控制是否 visible
                html_display  # ✅ 设置 HTML 内容
            ],
        )
    # 文件上传按钮点击触发文件处理，结果显示在右侧其实就是功能1
    # 上传文件
    def handle_uploaded_file(file,  history, username="用户"):
        if not isinstance(history, dict):
            history = {}
        bot_type="题目答疑智能体"
        # ✅ 确保 bot_type 在 history 中有 key
        if bot_type not in history:
            history[bot_type] = []

        if file is None:
            return history[bot_type], history
        try:
            content = parse_file(file)
            if not content:
                content = "（文件解析成功，但未检测到文本内容）"
        except Exception as e:
            content = f"文件解析失败：{e}"

        history[bot_type].append({"role": "user", "content": content})
        agent = agent_manager.get_agent("题目答疑智能体")

        response = agent.process(content)

        history[bot_type].append({"role": "assistant", "content": response})

        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            gr.update(value="题目答疑智能体"),  # ✅ 下拉框选中“题目答疑智能体”
            history[bot_type], history

        )
    upload_btn.click(
        fn=handle_uploaded_file,
        inputs=[file_upload, history, user_input],  # 或传一个默认 username 占位
        outputs=[
            chat_area,
            chapter_rag_area,
            flowchart_area,
            exercise_area,
            html_display,  # ✅ 控制是否 visible
            html_display,  # ✅ 设置 HTML 内容
            bot_dropdown,
            chat_display,
            history
        ]
    )
# 启动服务
demo.launch()

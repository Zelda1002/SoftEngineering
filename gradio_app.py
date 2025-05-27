import gradio as gr
import os
from agents import AgentManager, AGENT_CLASSES  # 导入你的智能体管理器和类定义

# 创建智能体管理器实例
agent_manager = AgentManager()


# 聊天回应逻辑
def chatbot_response(user_message, bot_type, history):
    agent = agent_manager.get_agent(bot_type)
    if agent:
        response = agent.process(user_message)
    else:
        response = f"没有找到名为 {bot_type} 的智能体。"
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response})
    return history, history


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


# HTML 内容列表（功能2,4,5）
html_contents = [
    None,  # 功能1是聊天，不是HTML
    """
    <h2>章节思维导图</h2>
    <iframe src="http://119.3.225.124:50/swdt0.html" style="width:100%; height:calc(100vh - 80px); border:none;"></iframe>
    """,
    None,  # 功能3现在是章节RAG，不是HTML
    """
    <h2 style="color:#6b5700;">功能4的标题</h2>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; color:#3f3a00;">
        <tr><th>姓名</th><th>年龄</th></tr>
        <tr><td>张三</td><td>25</td></tr>
        <tr><td>李四</td><td>30</td></tr>
    </table>
    """,
    """
    <h2 style="color:#6b5700;">功能5的标题</h2>
    <p style="color:#3f3a00;">功能5可以写任何HTML，自定义样式和结构。</p>
    """,
]

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
        with gr.Column(elem_id="sidebar", scale=1, min_width=200):
            gr.Markdown("<h2>软件工程课程助手</h2>", elem_id="sidebar_title")
            names = ["智能问答", "思维导图", "章节问答", "功能四", "功能五"]
            btns = [gr.Button(names[i], elem_id=f"btn_{i}") for i in range(5)]

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
                        placeholder="输入你的问题...", show_label=False, lines=2,
                        scale=8
                    )
                    send_button = gr.Button("发送", scale=2)

                history = gr.State([])

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
                        placeholder="输入你的问题...", show_label=False, lines=2,
                        scale=8
                    )
                    chapter_send_button = gr.Button("发送", scale=2)

                chapter_history = gr.State([])

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
                chapter_send_button.click(lambda: "", None, chapter_user_input)

            # 功能2,4,5：HTML 显示
            html_display = gr.HTML(html_contents[1], visible=False)

    # 功能切换逻辑
    def toggle_view(idx):
        if idx == 0:
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
            )
        elif idx == 2:  # 功能3 - 章节RAG
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
            )
        else:  # 功能2,4,5 - HTML显示
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True, value=html_contents[idx]),
            )

    # 为每个按钮绑定点击事件
    for i, btn in enumerate(btns):
        btn.click(
            fn=lambda i=i: toggle_view(i),
            inputs=[],
            outputs=[chat_area, chapter_rag_area, html_display],
        )


# 启动服务
demo.launch()

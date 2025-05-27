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

# HTML 内容列表（功能2-5）
html_contents = [
    None,  # 功能1是聊天，不是HTML
    """
    <h2>功能2: D3 折叠思维导图</h2>
    <iframe src="http://119.3.225.124:50/swdt0.html" style="width:100%; height:600px; border:none;"></iframe>
    """,
    """
    <h2 style="color:#6b5700;">功能3的标题</h2>
    <p style="color:#3f3a00;">功能3这里放一张图片：</p>
    <img src="https://gradio.app/assets/branding/wordmark-horizontal.svg" alt="Gradio Logo" width="200">
    """,
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
    """
]

# 自定义样式
css = """
    body, html {
        margin: 0; padding: 0; height: 100%;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        background-color: #fffef5;
        color: #4b4500;
        user-select: none;
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
"""

# 构建主界面
with gr.Blocks(css=css) as demo:
    with gr.Row():
        with gr.Column(elem_id="sidebar", scale=1, min_width=200):
            gr.Markdown("<h2>课程助手</h2>", elem_id="sidebar_title")
            btns = [gr.Button(f"功能{i+1}", elem_id=f"btn_{i}") for i in range(5)]

        with gr.Column(elem_id="content", scale=5) as content_area:
            # 功能1：聊天模块
            with gr.Column(visible=True) as chat_area:
                gr.Markdown("<h2 style='color:#6b5700;'>功能1: 智能对话</h2>")
                bot_dropdown = gr.Dropdown(
                    choices=list(AGENT_CLASSES.keys()),
                    label="选择机器人",
                    value="概念解释智能体"
                )
                chat_display = gr.Chatbot(type="messages")
                user_input = gr.Textbox(placeholder="输入你的问题...", label="提问", lines=1)
                send_button = gr.Button("发送")
                history = gr.State([])

                send_button.click(
                    chatbot_response,
                    inputs=[user_input, bot_dropdown, history],
                    outputs=[chat_display, history]
                )
                send_button.click(lambda: "", None, user_input)

            # 功能2~5：HTML 显示
            html_display = gr.HTML(html_contents[1], visible=False)

    # 功能切换逻辑
    # 功能切换逻辑（chat_area 和 html_display 二选一显示）
    def toggle_view(idx):
        if idx == 0:
            return gr.update(visible=True), gr.update(visible=False)
        else:
            return gr.update(visible=False), gr.update(visible=True, value=html_contents[idx])

    # 为每个按钮绑定点击事件
    for i, btn in enumerate(btns):
        btn.click(
            fn=lambda i=i: toggle_view(i),
            inputs=[],
            outputs=[chat_area, html_display]
        )


# 启动服务
demo.launch()

import gradio as gr
from agents import AgentManager, AGENT_CLASSES  # 导入智能体管理器和智能体类

# 创建智能体管理器实例
agent_manager = AgentManager()

# 定义机器人的初步回应
def chatbot_response(user_message, bot_type, history):
    # 根据选择的 bot_type 获取对应的智能体
    agent = agent_manager.get_agent(bot_type)
    
    if agent:
        # 调用智能体的 process 方法生成响应
        response = agent.process(user_message)
    else:
        # 如果没有找到对应的智能体，返回默认响应
        response = f"没有找到名为 {bot_type} 的智能体。"

    # 更新聊天记录：用户消息在右，机器人消息在左
    history.append({"role": "user", "content": user_message})  # 用户提问
    history.append({"role": "assistant", "content": response})  # 机器人回应
    
    return history, history  # 返回聊天记录更新后的状态

# 构建 Gradio 接口
def build_interface():
    with gr.Blocks(css=".gradio-container { background-color: #FFF9E6; }") as demo:  # 设置淡黄色背景
        gr.Markdown("<h1 style='text-align: center; color: black;'>软件工程课程助手</h1>")  # 标题
        
        # 创建一个选择机器人种类的下拉框，填充 AGENT_CLASSES 中的机器人类型
        bot_dropdown = gr.Dropdown(
            choices=list(AGENT_CLASSES.keys()),  # 从 AGENT_CLASSES 中获取机器人类型作为选项
            label="选择机器人",
            value="概念解释智能体"  # 默认选项
        )
        
        # 聊天记录区域
        chat_area = gr.Chatbot(type="messages")  # 使用 messages 类型，确保消息的角色和内容明确

        # 用户输入框和发送按钮
        user_input = gr.Textbox(placeholder="输入你的问题...", label="提问", lines=1)
        send_button = gr.Button("发送")
        
        # 初始化聊天记录
        history = gr.State([])  # 使用 gr.State() 来管理聊天记录
        
        # 将输入框和按钮事件与聊天记录关联，并清空输入框内容
        send_button.click(
            chatbot_response, 
            inputs=[user_input, bot_dropdown, history], 
            outputs=[chat_area, history]
        )
        
        # 清空输入框中的内容
        send_button.click(lambda: "", inputs=[], outputs=[user_input])

    return demo

# 启动 Gradio 接口
interface = build_interface()
interface.launch(share=True)
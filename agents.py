from client_hw import get_model_response

# RAG 相关的类和函数
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

persist_directory = "/Users/larry/Library/CloudStorage/GoogleDrive-larrylcccc@gmail.com/My Drive/USTB Course/SE Curriculum Design/local_txt_chroma_db"  # 假设它与脚本在同一目录中
collection_name = "local_documents_collection"  # 使用创建时使用的相同集合名称

embeddings_model_instance = None
vertor_store_instance = None

if openai_api_key:
    if os.path.exists(persist_directory):
        try:
            embeddings_model_instance = OpenAIEmbeddings(
                api_key=openai_api_key,
                model="text-embedding-3-large",  # 确保与创建数据库时使用的模型一致
            )
            vector_store_instance = Chroma(
                collection_name=collection_name,
                persist_directory=persist_directory,
                embedding_function=embeddings_model_instance,
            )
            print("Chroma 数据库已成功加载用于 RAG。")
        except Exception as e:
            print(f"初始化 RAG 组件时出错: {e}。RAG 功能可能受限。")
            vector_store_instance = None  # 确保出错时实例为None
    else:
        print(
            f"警告: Chroma 数据库目录 '{persist_directory}' 未找到。RAG 将不检索上下文。"
        )
        vector_store_instance = None
else:
    print("警告: 未配置 OPENAI_API_KEY。RAG 上下文检索功能将不可用。")
    vector_store_instance = None


# 基础的智能体类
class Agent:
    def __init__(self, name: str, description: str, system_prompt: str):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt

    def process(self, user_input: str) -> str:
        retrieved_context_str = (
            "本地知识库中没有找到相关信息。"  # 如果RAG失败或未找到文档的默认信息
        )

        if vector_store_instance and embeddings_model_instance:
            try:
                # 1. 从 ChromaDB 检索相关文档
                # 你可以调整 k 的值来控制检索文档的数量
                retrieved_docs = vector_store_instance.similarity_search(
                    user_input, k=12
                )

                if retrieved_docs:
                    # 将检索到的文档内容拼接起来
                    retrieved_context_str = "\n\n".join(
                        [doc.page_content for doc in retrieved_docs]
                    )
                    print(
                        f"为查询 '{user_input[:50]}...' 检索到的上下文片段: \n{retrieved_context_str[:200]}..."
                    )
                else:
                    print(
                        f"未能为查询 '{user_input[:50]}...' 从本地知识库检索到任何文档。"
                    )
            except Exception as e:
                print(f"从 ChromaDB 检索时出错: {e}")
                retrieved_context_str = "检索本地知识库信息时发生错误。"
        else:
            print("RAG 组件未初始化，跳过本地知识库检索。")

        # 2. 构建最终传递给 LLM 的用户输入
        # 包含原始系统提示的角色定义、检索到的上下文以及用户的原始问题

        # 智能体的 system_prompt 保持不变，定义其角色和行为指令
        # 我们将检索到的上下文和用户问题组合成一个新的 user_content
        final_user_input_for_llm = (
            f"请参考以下背景知识（如果与问题相关），主要根据背景知识回答：\n"
            f"--- 背景知识开始 ---\n"
            f"{retrieved_context_str}\n"
            f"--- 背景知识结束 ---\n\n"
            f"现在，请根据你的角色设定，并结合以上背景知识（如果相关），回答用户提出的以下问题：\n"
            f"{user_input}"
        )

        # 3. 调用 get_model_response 函数，传递智能体的原始 system_prompt 和增强后的用户输入
        return get_model_response(self.system_prompt, final_user_input_for_llm)


# 示例智能体1: 概念解释智能体
class ConceptExplanationAgent(Agent):
    def __init__(self):
        super().__init__(
            "概念解释智能体",
            "提供软件工程中各类概念和术语的解释。",
            "你是一个专业的软件工程助手，专门负责解释软件工程中的各类概念和术语。你将根据用户的提问提供简洁且准确的定义、背景知识以及相关的应用实例。你需要确保回答逻辑清晰，尽量举例帮助用户理解，并且保证所给出的解释符合学术界的标准。",
        )


# 示例智能体2: 需求分析智能体
class RequirementAnalysisAgent(Agent):
    def __init__(self):
        super().__init__(
            "需求分析智能体",
            "根据软件系统描述，提供全面的需求分析。",
            "你是一个软件工程领域的需求分析专家。当用户提供一个软件系统的描述时，你需要基于软件工程的理论与实践，进行全面的需求分析。包括但不限于：\n- 功能需求分析\n- 非功能需求分析\n- 用户需求与系统需求的区分\n- 系统的技术、性能和安全需求\n你将结合业务目标、技术限制和用户需求，提出合理的解决方案，确保分析结果准确且可实施。",
        )


# 示例智能体3: 软件设计智能体
class SoftwareDesignAgent(Agent):
    def __init__(self):
        super().__init__(
            "软件设计智能体",
            "为软件系统提供架构方案和设计文档。",
            "你是一个经验丰富的软件设计专家。根据用户提供的系统描述，你需要为系统设计一个全面的架构方案，并提供详细的设计文档。设计过程中需考虑以下内容：\n- 系统架构设计（如微服务架构、客户端-服务器架构等）\n- 模块设计与功能分配\n- 数据库设计（如ER图、数据库表设计）\n- 交互设计与UI原型\n- 系统扩展性和可维护性设计\n你的回答需要详细阐明设计原则，保证设计方案的高效性、可扩展性与稳定性。",
        )


# 示例智能体4: 软件测试智能体
class SoftwareTestingAgent(Agent):
    def __init__(self):
        super().__init__(
            "软件测试智能体",
            "根据软件系统描述，提供测试策略和方法。",
            "你是一个软件测试专家，负责根据用户描述的系统来设计和建议相关的测试策略和方法。你需要根据软件的功能、性能要求以及用户需求，设计以下测试活动：\n- 单元测试、集成测试、系统测试和验收测试\n- 性能测试、安全测试、兼容性测试\n- 自动化测试脚本的设计与实现\n你需要确保测试方法的全面性、有效性，并且能够识别潜在的风险点，保证软件质量。",
        )


# 示例智能体5: 题目答疑智能体
class ExamQuestionAnswerAgent(Agent):
    def __init__(self):
        super().__init__(
            "题目答疑智能体",
            "解答软件工程课程相关练习题。",
            "你是一个软件工程课程的答疑助手。用户将输入一个具体的练习题或概念问题，你需要基于课本内容和专业知识进行解答。你应提供以下内容：\n- 清晰的答案\n- 解题思路和步骤\n- 相关理论背景或知识点的解释\n确保你的回答详尽、准确并且符合课程教材要求，能够帮助学生掌握相关的知识点。",
        )


# 创建智能体选择映射
AGENT_CLASSES = {
    "概念解释智能体": ConceptExplanationAgent,
    "需求分析智能体": RequirementAnalysisAgent,
    "软件设计智能体": SoftwareDesignAgent,
    "软件测试智能体": SoftwareTestingAgent,
    "题目答疑智能体": ExamQuestionAnswerAgent,
}


# 创建一个智能体管理器
class AgentManager:
    def __init__(self):
        self.agents = {name: agent() for name, agent in AGENT_CLASSES.items()}

    def get_agent(self, agent_name: str) -> Agent:
        return self.agents.get(agent_name, None)

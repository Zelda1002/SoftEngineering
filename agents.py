from client_hw import get_model_response

# RAG 相关的类和函数
from langchain_embed_siliconflow import SiliconFlowEmbeddings
#from langchain.vectorstores import Chroma
from langchain_community.vectorstores import Chroma

from dotenv import load_dotenv
import os
import use_neo4j
# 加载环境变量
load_dotenv()
silicon_api_key = os.getenv("SILICON_API_KEY")

persist_directory = "./local_pdf_chroma_db_sf"
collection_name = "sf_pdf_documents_collection"

embeddings_model_instance = None
vector_store_instance = None

if silicon_api_key:
    if os.path.exists(persist_directory):
        try:
            embeddings_model_instance = SiliconFlowEmbeddings(
                api_key=silicon_api_key,
                model_name="BAAI/bge-large-zh-v1.5",
            )
            vector_store_instance = Chroma(
                collection_name=collection_name,
                persist_directory=persist_directory,
                embedding_function=embeddings_model_instance,
            )
            print("Chroma 数据库已成功加载用于 RAG (使用 SiliconFlow)。")
        except Exception as e:
            print(f"初始化 RAG 组件 (SiliconFlow) 时出错: {e}。RAG 功能可能受限。")
            vector_store_instance = None
    else:
        print(
            f"警告: Chroma 数据库目录 '{persist_directory}' 未找到。RAG 将不检索上下文。"
        )
        vector_store_instance = None
else:
    print("警告: 未配置 SILICON_API_KEY。RAG 上下文检索功能将不可用。")
    vector_store_instance = None


# 基础的智能体类
class Agent:
    def __init__(self, name: str, description: str, system_prompt: str):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt

    def process(self, user_input: str, selected_chapter: str = None) -> str:
        neo4j_entity = use_neo4j.query_from_neo4j(user_input)
        if len(neo4j_entity) > 0:
            for entity in neo4j_entity:
                user_input += ','
                user_input += entity
        print("用户输入：",user_input)
        retrieved_context_str = "本地知识库中没有找到相关信息。"
        actual_retrieved_docs = []
        if vector_store_instance and embeddings_model_instance:
            try:
                # 构建查询，如果选择了章节则包含章节信息
                query = user_input
                if selected_chapter and selected_chapter != "全部章节":
                    query = f"第{selected_chapter}章 {user_input}"

                retrieved_docs_from_db = vector_store_instance.similarity_search(
                    query, k=12
                )

                # 如果指定了章节，进一步过滤结果
                if (
                    selected_chapter
                    and selected_chapter != "全部章节"
                    and retrieved_docs_from_db
                ):
                    filtered_docs = []
                    for doc in retrieved_docs_from_db:
                        if hasattr(doc, "metadata") and doc.metadata:
                            # 假设文档的metadata中包含章节信息
                            doc_content = doc.page_content.lower()
                            chapter_keywords = [
                                f"第{selected_chapter}章",
                                f"chapter {selected_chapter}",
                                f"第 {selected_chapter} 章",
                            ]
                            if any(
                                keyword in doc_content for keyword in chapter_keywords
                            ):
                                filtered_docs.append(doc)

                    # 如果过滤后没有结果，使用原始检索结果但数量减少
                    if filtered_docs:
                        retrieved_docs_from_db = filtered_docs[:8]
                    else:
                        retrieved_docs_from_db = retrieved_docs_from_db[:6]

                if retrieved_docs_from_db:
                    actual_retrieved_docs = retrieved_docs_from_db
                    retrieved_context_str = "\n\n".join(
                        [doc.page_content for doc in actual_retrieved_docs]
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

        # 构建最终传递给 LLM 的用户输入
        chapter_context = (
            f"请重点关注第{selected_chapter}章的内容。"
            if selected_chapter and selected_chapter != "全部章节"
            else ""
        )

        final_user_input_for_llm = (
            f"{chapter_context}\n"
            f"请参考以下背景知识（如果与问题相关），主要根据背景知识回答：\n"
            f"--- 背景知识开始 ---\n"
            f"{retrieved_context_str}\n"
            f"--- 背景知识结束 ---\n\n"
            f"现在，请根据你的角色设定，并结合以上背景知识（如果相关），回答用户提出的以下问题：\n"
            f"{user_input}"
        )

        llm_response = get_model_response(self.system_prompt, final_user_input_for_llm)

        # 处理API调用失败的情况
        if llm_response is None:
            llm_response = f"抱歉，AI服务暂时不可用。但我找到了以下相关资料供您参考：\n\n根据检索到的资料，关于您询问的问题，可以参考以下内容。"

        # 在LLM回答后附加RAG检索到的上下文片段和页码
        appendix_header = "\n\n--- 参考的上下文片段 ---"
        appendix_content = ""

        if actual_retrieved_docs:
            for i, doc in enumerate(actual_retrieved_docs):
                page_number = "未知页码"
                if hasattr(doc, "metadata") and doc.metadata:
                    page_number_val = doc.metadata.get("page")
                    if page_number_val is not None:
                        page_number = str(page_number_val)

                page_content_cleaned = doc.page_content
                page_content_cleaned = (
                    page_content_cleaned.replace("\r\n", " ")
                    .replace("\n", " ")
                    .replace("\r", " ")
                )
                page_content_cleaned = " ".join(page_content_cleaned.split())
                page_content_cleaned = page_content_cleaned.strip()

                appendix_content += (
                    f"\n\n片段 {i+1} (来自页码: {page_number}):\n{page_content_cleaned}"
                )
        elif vector_store_instance and embeddings_model_instance:
            appendix_content = "\n未从本地知识库中检索到与查询直接相关的上下文片段。"
        else:
            appendix_content = "\n本地知识库未启用或初始化失败，未检索上下文。"

        #return llm_response
        #回答出参考的上下文片段
        return llm_response + appendix_header + appendix_content


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

#智能体6: 出题智能体
class ExerciseGenerationAgent(Agent):
    def __init__(self):
        super().__init__(
            "出题智能体",
            "根据章节、知识点和难度生成题目、答案与解析。",
            "你是一个软件工程课程的智能出题助手。用户将选择章节、知识点和难度等级，你需要基于这些条件生成一道与之匹配的题目，连同标准答案和详细解析。\n"
            "生成格式如下：\n"
            "【题目】...\n"
            "【答案】...\n"
            "【解析】...\n"
            "确保题目原创、针对性强、表达清晰，并具有教学价值。"
        )

    def process(self, user_input: str,
                selected_chapter: str = None,
                selected_topic: str = None,
                difficulty: str = "中等",
                question_type: str = None  # 新增题型参数
                ) -> str:
        chapter_info = f"第{selected_chapter}章" if selected_chapter else ""
        topic_info = f"知识点：{selected_topic}" if selected_topic else ""
        qtype_info = f"题型：{question_type}" if question_type else ""

        prompt = (
            f"请基于以下信息出一道题目：\n"
            f"{chapter_info}\n{topic_info}\n{qtype_info}\n难度：{difficulty}\n"
            f"要求生成题目+答案+解析，格式如下：\n"
            f"【题目】...\n【答案】...\n【解析】...\n"
        )
        return get_model_response(self.system_prompt, prompt)



# 创建智能体选择映射
AGENT_CLASSES = {
    "概念解释智能体": ConceptExplanationAgent,
    "需求分析智能体": RequirementAnalysisAgent,
    "软件设计智能体": SoftwareDesignAgent,
    "软件测试智能体": SoftwareTestingAgent,
    "题目答疑智能体": ExamQuestionAnswerAgent,
    "出题智能体": ExerciseGenerationAgent,
}


# 创建一个智能体管理器
class AgentManager:
    def __init__(self):
        self.agents = {name: agent() for name, agent in AGENT_CLASSES.items()}

    def get_agent(self, agent_name: str) -> Agent:
        return self.agents.get(agent_name, None)

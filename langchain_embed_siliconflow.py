import os
import time  # For potential rate limiting
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from typing import List
import requests
import json


# --- Custom SiliconFlow Embeddings Class ---
class SiliconFlowEmbeddings(Embeddings):
    def __init__(
        self,
        api_key: str,
        model_name: str = "BAAI/bge-large-zh-v1.5",
        api_base_url: str = "https://api.siliconflow.cn/v1",
        batch_size: int = 32,  # Adjust based on API limits or performance
        request_timeout: int = 60,  # Timeout for API requests in seconds
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = f"{api_base_url}/embeddings"
        self.batch_size = batch_size
        self.request_timeout = request_timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeds a single batch of texts."""
        payload = {
            "model": self.model_name,
            "input": texts,  # API docs suggest 'input' can be a list of strings for batching
            "encoding_format": "float",
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=self.request_timeout,
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            response_data = response.json()

            if "data" in response_data and isinstance(response_data["data"], list):
                # Ensure embeddings are sorted in the same order as input texts
                # The API should return them in order, but good to be mindful
                # For BGE models, the dimension is often 1024 for -large, 768 for -base
                # It's safer to get dimension from first embedding if possible, or assume
                # For BAAI/bge-large-zh-v1.5, dimension is 1024
                embeddings = [item["embedding"] for item in response_data["data"]]
                if len(embeddings) == len(texts):
                    return embeddings
                else:
                    print(
                        f"Warning: Mismatch in number of embeddings received ({len(embeddings)}) vs texts sent ({len(texts)})."
                    )
                    # Fallback: return empty embeddings or raise error
                    return [
                        [0.0] * 1024 for _ in texts
                    ]  # Placeholder, adjust dimension
            else:
                print(
                    f"Error: Unexpected response format from SiliconFlow API: {response_data}"
                )
                return [[0.0] * 1024 for _ in texts]  # Placeholder

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred while embedding: {http_err}")
            print(f"Response content: {response.content.decode()}")
            return [[0.0] * 1024 for _ in texts]  # Placeholder
        except requests.exceptions.Timeout:
            print(f"Request timed out while embedding batch.")
            return [[0.0] * 1024 for _ in texts]  # Placeholder
        except Exception as e:
            print(f"An error occurred while embedding batch: {e}")
            return [[0.0] * 1024 for _ in texts]  # Placeholder

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            print(
                f"Embedding batch {i // self.batch_size + 1}/{(len(texts) -1) // self.batch_size + 1}, size: {len(batch)}"
            )
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            # Optional: add a small delay to avoid hitting rate limits if any
            # time.sleep(0.1)
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        # For a single query, the API expects 'input' to be a string, not a list.
        payload = {
            "model": self.model_name,
            "input": text,
            "encoding_format": "float",
        }
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            response_data = response.json()
            if (
                "data" in response_data
                and isinstance(response_data["data"], list)
                and len(response_data["data"]) > 0
            ):
                return response_data["data"][0]["embedding"]
            else:
                print(f"Error: Unexpected response format for query: {response_data}")
                return [0.0] * 1024  # Placeholder, adjust dimension
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred while embedding query: {http_err}")
            print(f"Response content: {response.content.decode()}")
            return [0.0] * 1024  # Placeholder
        except requests.exceptions.Timeout:
            print(f"Request timed out while embedding query.")
            return [0.0] * 1024  # Placeholder
        except Exception as e:
            print(f"An error occurred while embedding query: {e}")
            return [0.0] * 1024  # Placeholder


# --- Main script logic ---
# This part will only run when the script is executed directly
if __name__ == "__main__":
    load_dotenv()
    silicon_api_key = os.getenv("SILICON_API_KEY")
    silicon_base_url = "https://api.siliconflow.cn/v1"

    if not silicon_api_key:
        raise ValueError(
            "在环境变量中未找到 SILICON_API_KEY。请在您的 .env 文件中设置它。"
        )

    pdf_files_directory = "./textbook"
    persist_directory = "./local_pdf_chroma_db_sf"  # Changed to avoid conflict
    collection_name = "sf_pdf_documents_collection"  # Changed to avoid conflict

    # 使用自定义的 SiliconFlowEmbeddings 类
    embeddings = SiliconFlowEmbeddings(
        api_key=silicon_api_key,
        api_base_url=silicon_base_url,
        model_name="BAAI/bge-large-zh-v1.5",
        batch_size=16,  # SiliconFlow docs mention a limit of 2048 tokens per request,
        # and input array length max 256. Batching texts is safer.
        # A batch_size of 16-32 texts should be reasonable.
    )

    print(f"正在目录中查找 .pdf 文件: {pdf_files_directory}")

    if not os.path.isdir(pdf_files_directory):
        print(f"错误：目录 {pdf_files_directory} 未找到")
        print("请创建此目录并将您的 .pdf 文件放入其中，或更正路径。")
    else:
        loader = DirectoryLoader(
            pdf_files_directory,
            glob="**/*.pdf",
            show_progress=True,
            loader_cls=PyPDFLoader,
        )

        print(f"正在从 '{pdf_files_directory}' 加载 PDF 文档...")
        documents = loader.load()

        if not documents:
            print(
                f"在 {pdf_files_directory} 中未找到 .pdf 文件。请确保文件存在且 glob 模式正确。"
            )
        else:
            print(f"已加载 {len(documents)} 个 PDF 文档。")

            # Filter out any documents that might be None or have no page_content
            valid_documents = [
                doc
                for doc in documents
                if doc and hasattr(doc, "page_content") and doc.page_content.strip()
            ]
            if len(valid_documents) != len(documents):
                print(
                    f"警告: 移除了 {len(documents) - len(valid_documents)} 个无效或空的文档。"
                )

            if not valid_documents:
                print("没有有效的文档内容可供处理。")
            else:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,  # Reduced chunk_size to better fit token limits per item in batch
                    chunk_overlap=100,
                )
                all_splits = text_splitter.split_documents(valid_documents)
                # Further filter: ensure no split is just whitespace
                all_splits = [
                    split for split in all_splits if split.page_content.strip()
                ]

                if not all_splits:
                    print("分割后没有有效的文本块可供嵌入。")
                else:
                    print(f"已将 PDF 文档分割成 {len(all_splits)} 个有效文本块。")

                    print(
                        f"正在初始化 Chroma 数据库于: {persist_directory}，集合名称: {collection_name} (使用自定义硅基流动嵌入)"
                    )

                    # Ensure all_splits contains Document objects with page_content
                    # The custom embedder expects List[str], Chroma.from_documents expects List[Document]
                    # The custom class's embed_documents method will handle extracting page_content if we pass List[Document]
                    # However, Chroma.from_documents will call embeddings.embed_documents([doc.page_content for doc in documents])
                    # So our SiliconFlowEmbeddings.embed_documents needs to correctly handle a list of strings.

                    vector_store = Chroma.from_documents(
                        documents=all_splits,  # List of Document objects
                        embedding=embeddings,  # Our custom embeddings class
                        collection_name=collection_name,
                        persist_directory=persist_directory,
                    )

                    print(
                        f"已成功在 '{persist_directory}' 创建并持久化 Chroma 数据库 (集合为 '{collection_name}')，使用硅基流动嵌入模型处理 PDF。"
                    )
                    print("您现在可以打包此目录以进行共享。")

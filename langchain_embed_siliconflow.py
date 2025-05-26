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
                embeddings = [item["embedding"] for item in response_data["data"]]
                if len(embeddings) == len(texts):
                    return embeddings
                else:
                    print(
                        f"Warning: Mismatch in number of embeddings received ({len(embeddings)}) vs texts sent ({len(texts)})."
                    )
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

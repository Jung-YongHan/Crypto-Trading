import os
from typing import Union
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient


def get_model_client(
    model_name: str,
) -> Union[OpenAIChatCompletionClient, OllamaChatCompletionClient]:
    """
    모델 이름에 따라 적절한 모델 클라이언트를 반환합니다.
    """
    if model_name.startswith("gpt") or model_name.startswith("o"):
        return OpenAIChatCompletionClient(
            model=model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    else:
        return OllamaChatCompletionClient(model=model_name)

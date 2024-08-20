import abc
from typing import List, Dict, Any
import anthropic
import openai
from model_cache import load_cached_models, save_cached_models

class APIService(abc.ABC):
    @abc.abstractmethod
    def call_api(self, content: str, model: str, max_tokens: int, temperature: float) -> str:
        pass

    @abc.abstractmethod
    def get_available_models(self) -> List[str]:
        pass

    @abc.abstractmethod
    def get_max_tokens(self, model: str) -> int:
        pass

class AnthropicService(APIService):
    def __init__(self, api_key: str):
        # Ensure the API key is passed correctly
        self.client = anthropic.Anthropic(api_key=api_key)

    def call_api(self, content: str, model: str, max_tokens: int, temperature: float) -> str:
        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": content}
                ]
            )
            return message.content[0].text if message.content else ""
        except anthropic.APIConnectionError as e:
            print(f"Error calling Anthropic API: {e}")
            return "I apologize, but I'm having trouble connecting to my knowledge base right now. Please try again later."

    def get_available_models(self) -> List[str]:
        cached_models = load_cached_models('Anthropic')
        if cached_models:
            return cached_models

        models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
        save_cached_models('Anthropic', models)
        return models

    def get_max_tokens(self, model: str) -> int:
        # Ensure all Anthropic models are set to 4096
        return 4096

class OpenAIService(APIService):
    def __init__(self, api_key: str):
        # Ensure the API key is passed correctly
        self.client = openai.OpenAI(api_key=api_key)

    def call_api(self, content: str, model: str, max_tokens: int, temperature: float) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": content}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except openai.APIConnectionError as e:
            print(f"Error calling OpenAI API: {e}")
            return "I apologize, but I'm having trouble connecting to my knowledge base right now. Please try again later."

    def get_available_models(self) -> List[str]:
        cached_models = load_cached_models('OpenAI')
        if cached_models:
            return cached_models

        try:
            models = self.client.models.list()
            chat_models = [model.id for model in models if model.id.startswith("gpt-")]
            sorted_models = sorted(chat_models)
            save_cached_models('OpenAI', sorted_models)
            return sorted_models
        except openai.APIConnectionError as e:
            print(f"Error fetching models: {e}")
            return [
                "gpt-4-0125-preview",
                "gpt-4-turbo-preview",
                "gpt-4-1106-preview",
                "gpt-4-vision-preview",
                "gpt-4",
                "gpt-4-0314",
                "gpt-4-0613",
                "gpt-4-32k",
                "gpt-4-32k-0314",
                "gpt-4-32k-0613",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-3.5-turbo-0301",
                "gpt-3.5-turbo-0613",
                "gpt-3.5-turbo-1106",
                "gpt-3.5-turbo-16k-0613"
            ]

    def get_max_tokens(self, model: str) -> int:
        max_tokens = {
            "gpt-4-0125-preview": 128000,
            "gpt-4-turbo-preview": 128000,
            "gpt-4-1106-preview": 128000,
            "gpt-4-vision-preview": 128000,
            "gpt-4": 8192,
            "gpt-4-0314": 8192,
            "gpt-4-0613": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-32k-0314": 32768,
            "gpt-4-32k-0613": 32768,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-3.5-turbo-0301": 4096,
            "gpt-3.5-turbo-0613": 4096,
            "gpt-3.5-turbo-1106": 16384,
            "gpt-3.5-turbo-16k-0613": 16384
        }
        # Set all OpenAI models to their maximum values
        return max_tokens.get(model, 128000)  # Default to 128000 if model not found

def get_service(service_name: str, api_key: str) -> APIService:
    if service_name == "Anthropic":
        return AnthropicService(api_key)
    elif service_name == "OpenAI":
        return OpenAIService(api_key)
    else:
        raise ValueError(f"Unknown service: {service_name}")

def get_available_services() -> List[str]:
    return ["Anthropic", "OpenAI"]
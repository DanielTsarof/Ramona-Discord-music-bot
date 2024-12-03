import asyncio
from typing import List
from abc import ABC, abstractmethod
import os

import aiohttp
import openai
import tiktoken
from ai21 import AsyncAI21Client
from ai21.tokenizers import get_tokenizer
from ai21.models.chat import ChatMessage

from src.config import Speech
from src.handlers.utils import get_paths


def get_prompt(path: str, max_length: int):
    with open(path) as f:
        prompt = f.readlines()
    prompt = prompt[0] + f' Максимальная длина твоего ответа: {max_length} слов.' \
                         f' Вот история диалога: '
    return prompt


class SpeechModelABC(ABC):
    def __init__(self, api_key: str, config: Speech):
        self.api_key = api_key
        self.dialogue_history: List[str] = []
        self.config = config
        self.prompt = get_prompt(f'src/prompts/{config.prompt}', config.ans_max_length)

    def change_prompt(self, name: str):
        """
        :param name: new prompt name
        """
        self.prompt = get_prompt(f'src/prompts/{name}.txt', self.config.ans_max_length)

    def show_personalities(self):
        """
        shows list of available personalities
        """
        names = [path.replace('.txt', '').split(os.sep)[-1] for path in get_paths('src/prompts', 'txt')]
        return '\n'.join(names)

    @abstractmethod
    def _count_tokens(self, string: str, model: str):
        pass

    @abstractmethod
    async def fetch_gpt_response(self, request: str):
        pass

    async def ask(self, question: str):
        self.dialogue_history.append(f"User: {question}")

        while True:
            dialogue_text = "\n".join(self.dialogue_history)
            if self._count_tokens(dialogue_text) > self.config.max_tokens:
                self.dialogue_history.pop(0)  # Удаление первого сообщения
            else:
                break

        request = self.prompt + dialogue_text

        answer = await self.fetch_gpt_response(request=request)

        self.dialogue_history.append(f"AI: {answer}")
        return answer.replace('AI: ', '')


class SpeechModelOpenAI(SpeechModelABC):

    def __init__(self, api_key: str, config: Speech):
        super().__init__(api_key, config)
        openai.api_key = api_key

    def _count_tokens(self, string: str, model: str = 'gpt-3.5-turbo') -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    async def fetch_gpt_response(self, request: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}",
        }
        data = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": request}],
            "max_tokens": self.config.max_tokens,
            "n": 1,
            "stop": None,
            "temperature": self.config.temperature,
            "top_p": 1,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    json_response = await response.json()
                    return json_response["choices"][0]["message"]["content"]
                else:
                    error_message = await response.text()
                    raise Exception(f"API request failed with status {response.status}. Error message: {error_message}")


class SpeechModelA21(SpeechModelABC):

    def __init__(self, api_key: str, config: Speech):
        super().__init__(api_key, config)
        self.client = AsyncAI21Client(api_key=api_key)
        if 'jamba' in self.config.model:
            self.tokenizer = get_tokenizer(name=f"jamba-tokenizer")
        elif 'j2' in self.config.model:
            self.tokenizer = get_tokenizer(name=f"j2-tokenizer")
        else:
            raise ValueError(f'Model {self.config.model} is not supported!')


    def _count_tokens(self, string: str, model: str="jamba-1.5-mini") -> int:
        total_tokens = self.tokenizer.count_tokens(text=string)  # returns int
        return total_tokens

    async def fetch_gpt_response(self, request: str) -> str:
        messages = [
            ChatMessage(content=request, role="user")
        ]
        response = await self.client.chat.completions.create(
            messages=messages,
            model="jamba-1.5-mini",
        )

        return response.choices[0].message.content


def get_speech_model(provider: str, config: Speech, api_key:str) -> SpeechModelABC:
    if provider == 'openai':
        return SpeechModelOpenAI(api_key, config)
    elif provider == 'ai21':
        return SpeechModelA21(api_key, config)
    else:
        raise ValueError(f'Provider {provider} if not supported!')
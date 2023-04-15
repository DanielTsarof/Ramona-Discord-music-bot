from typing import List

import aiohttp
import openai
import tiktoken

from src.config import Speech


def get_prompt(path: str, max_length: int):
    with open(path) as f:
        prompt = f.readlines()
    prompt = prompt[0] + f' Максимальная длина твоего ответа: {max_length} слов.' \
                         f' Вот история диалога: '
    return prompt


class SpeechModel:

    def __init__(self, api_key: str, config: Speech):
        openai.api_key = api_key
        self.dialogue_history: List[str] = []
        self.config = config
        self.prompt = get_prompt(f'src/prompts/{config.prompt}', config.ans_max_length)

    def _count_tokens(self, string: str, model: str = 'gpt-3.5-turbo') -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def change_prompt(self, name: str):
        self.prompt = get_prompt(f'src/prompts/{name}.txt', self.config.ans_max_length)

    async def fetch_gpt_response(self, request: str):
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

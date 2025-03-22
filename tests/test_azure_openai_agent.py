import pytest

import auth
from azure_openai_agent import Conversation
from openai import AzureOpenAI
import json


def test_azure_openai_agent():
    cookies_path = "raw/cookies.csv"
    cookies = auth.load_cookies(cookies_path)
    conv = Conversation(cookies=cookies, max_func_call_rounds=5)
    conv.answer_query("搜 Minecraft Cubeez 奥克兰本周 给出帖子链接")
    print(conv.messages)


def test_chat_completion():
    with open("config.json") as f:
        config = json.load(f)
    client = AzureOpenAI(
        azure_endpoint=config.get('azure_endpoint'),
        api_key=config.get('azure_api_key'),
        api_version=config.get('azure_api_version'),
    )
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "I am going to Paris, what should I see?",
            }
        ],
        max_completion_tokens=100000,
        model=config.get('azure_deployment_name')
    )
    print(response.choices[0].message.content)


if __name__ == '__main__':
    pytest.main()

import json

from dto import ChatbotRequest
from samples import list_card
import aiohttp
import time
import logging
import openai
from dotenv import load_dotenv
import os
import requests

load_dotenv()
openai.api_key = os.getenv('GPT_KEY', '')
SYSTEM_MSG = "당신은 카카오 서비스 제공자입니다."
logger = logging.getLogger("Callback")


def callback_handler(request: ChatbotRequest) -> dict:
    url = request.userRequest.callbackUrl
    utterance = request.userRequest.utterance

    print("url : ", url)
    print("utterance : ", utterance)

    # ===================== start =================================
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": utterance},
        ],
        temperature=0,
    )
    # focus
    output_text = response.choices[0].message.content
    print(output_text)

    # 참고링크 통해 payload 구조 확인 가능
    payload = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": output_text
                    }
                }
            ]
        }
    }
    # ===================== end =================================
    # 참고링크1 : https://kakaobusiness.gitbook.io/main/tool/chatbot/skill_guide/ai_chatbot_callback_guide
    # 참고링크1 : https://kakaobusiness.gitbook.io/main/tool/chatbot/skill_guide/answer_json_format

    time.sleep(1.0)
    print(payload)

    if url:
        response = requests.post(
            url=url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        print(response)

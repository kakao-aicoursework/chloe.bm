import json
import os
import tkinter as tk
from tkinter import scrolledtext

import chromadb
import openai

openai.api_key = os.getenv('GPT_KEY', '')


def main():
    # 데이터 저장
    content = read_file('./resources/project_data_kakao_channel.txt')
    ids, documents = generate_date(content)
    collection = get_or_create_db("kakao-channel")
    save_data(collection, ids, documents)

    message_log = [
        {
            "role": "system",
            "content": '''
            You are a customer advisor. 
            If a user asks about a function they don’t know, you must kindly answer in Korean.
            '''
        }
    ]

    def show_popup_message(window, message):
        popup = tk.Toplevel(window)
        popup.title("")

        # 팝업 창의 내용
        label = tk.Label(popup, text=message, font=("맑은 고딕", 12))
        label.pack(expand=True, fill=tk.BOTH)

        # 팝업 창의 크기 조절하기
        window.update_idletasks()
        popup_width = label.winfo_reqwidth() + 20
        popup_height = label.winfo_reqheight() + 20
        popup.geometry(f"{popup_width}x{popup_height}")

        # 팝업 창의 중앙에 위치하기
        window_x = window.winfo_x()
        window_y = window.winfo_y()
        window_width = window.winfo_width()
        window_height = window.winfo_height()

        popup_x = window_x + window_width // 2 - popup_width // 2
        popup_y = window_y + window_height // 2 - popup_height // 2
        popup.geometry(f"+{popup_x}+{popup_y}")

        popup.transient(window)
        popup.attributes('-topmost', True)

        popup.update()
        return popup

    def on_send():
        user_input = user_entry.get()
        user_entry.delete(0, tk.END)

        if user_input.lower() == "quit":
            window.destroy()
            return

        message_log.append({"role": "user", "content": user_input})
        conversation.config(state=tk.NORMAL)  # 이동
        conversation.insert(tk.END, f"You: {user_input}\n", "user")  # 이동
        thinking_popup = show_popup_message(window, "처리중...")
        window.update_idletasks()
        # '생각 중...' 팝업 창이 반드시 화면에 나타나도록 강제로 설정하기
        response = chat(collection, message_log)
        thinking_popup.destroy()

        message_log.append({"role": "assistant", "content": response})

        # 태그를 추가한 부분(1)
        conversation.insert(tk.END, f"gpt assistant: {response}\n", "assistant")
        conversation.config(state=tk.DISABLED)
        # conversation을 수정하지 못하게 설정하기
        conversation.see(tk.END)

    window = tk.Tk()
    window.title("GPT AI")

    font = ("맑은 고딕", 10)

    conversation = scrolledtext.ScrolledText(window, wrap=tk.WORD, bg='#f0f0f0', font=font)
    # width, height를 없애고 배경색 지정하기(2)
    conversation.tag_configure("user", background="#c9daf8")
    # 태그별로 다르게 배경색 지정하기(3)
    conversation.tag_configure("assistant", background="#e4e4e4")
    # 태그별로 다르게 배경색 지정하기(3)
    conversation.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    # 창의 폭에 맞추어 크기 조정하기(4)

    input_frame = tk.Frame(window)  # user_entry와 send_button을 담는 frame(5)
    input_frame.pack(fill=tk.X, padx=10, pady=10)  # 창의 크기에 맞추어 조절하기(5)

    user_entry = tk.Entry(input_frame)
    user_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)

    send_button = tk.Button(input_frame, text="Send", command=on_send)
    send_button.pack(side=tk.RIGHT)

    window.bind('<Return>', lambda event: on_send())
    window.mainloop()


def read_file(file_name):
    with open(file_name, 'r') as f:
        content = f.read()
        return content


def generate_date(content):
    # 데이터 인덱스
    ids = []
    # 벡터로 변환 저장할 텍스트 데이터
    documents = []

    # 소제목 앞에 #이 붙어있으므로 그에 맞추어 자르기
    datas = content.strip().split("\n#")
    # 맨 첫줄에 나와있는 제목 형식이 '{content}: ' 이므로 그에 맞추어 자르기
    file_title = datas[0].strip().split(":")[0]

    for idx in range(1, len(datas)):
        # 첫 줄 소제목
        split_data = datas[idx].split('\n')
        data_title = split_data[0]
        # 소제목을 제외한 나머지 내용을 전부 content로 본다.
        del split_data[0]
        data_content = ''.join(split_data).replace('\n', '')
        ids.append(f'{file_title}-{idx}')
        documents.append(f'{data_title} : {data_content}')

    return ids, documents


def get_or_create_db(db_name):
    client = chromadb.PersistentClient()
    collection = client.get_or_create_collection(
        name=db_name,
        metadata={"hnsw:space": "cosine"}
    )

    return collection


def save_data(collection, ids, documents):
    # DB 저장
    collection.upsert(
        documents=documents,
        ids=ids
    )


def get_data(collection, query):
    # 쿼리 조회
    vector_datas = collection.query(
        query_texts=[query],
        n_results=1,
    )

    result = []
    for idx, data in enumerate(vector_datas['documents'][0]):
        item = data.split(':')
        result.append({
            "title": item[0].strip(),
            "content": item[1].strip()
        })

    return result


def chat(collection, message_log, gpt_model="gpt-3.5-turbo", temperature=0):
    response = data_call_func(message_log, gpt_model, temperature)
    print(json.dumps(response, ensure_ascii=False))

    if response.get("function_call"):
        if response["function_call"]["name"] == "get_data":
            message_log.append(response)

            arguments = json.loads(response.function_call.arguments)
            datas = get_data(collection, arguments['query'])

            message_log.append(
                {
                    "role": "function",
                    "name": "get_data",
                    "content": json.dumps(datas, ensure_ascii=False),
                }
            )

            response = openai.ChatCompletion.create(
                model=gpt_model,
                messages=message_log,
                temperature=temperature,
            )

        return response.choices[0].message.content

    else:
        return response.content


def data_call_func(message_log, gpt_model, temperature):
    functions = [
        {
            "name": "get_data",
            "description": "카카오톡 채널 기능 검색",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "질문 키워드",
                    }
                },
                "required": ["query"]
            }
        }
    ]

    completion = openai.ChatCompletion.create(
        model=gpt_model,
        messages=message_log,
        functions=functions,
        function_call="auto",
        temperature=temperature
    )

    return completion.choices[0].message


if __name__ == "__main__":
    main()

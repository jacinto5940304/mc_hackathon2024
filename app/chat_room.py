import tkinter as tk
from tkinter import ttk
import requests
from PIL import Image, ImageTk
from io import BytesIO
import pyttsx3
import speech_recognition as sr
import asyncio
import aiohttp
from tkinter import simpledialog
import threading
import os
import json
from google.cloud import vision
from tkinter import filedialog, messagebox


from vpet import Vpet
from WeatherService import weather_service
from TutorialApp import TutorialApp

# 你的 OpenAI API Key
api_key = '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'
weather_api_key = '92cd6be29821152b87d8c2ec5e3cccb6'

# 設定 Google Cloud Vision API 憑證
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './src/silver-theme-439105-i6-ac61c12c257b.json'
client = vision.ImageAnnotatorClient()

# 儲存生成的圖片以便下載
generated_image = None

# memory recorder
conversation_history = []
now_conversation = []


def load_conversation_history():
    global now_conversation
    global conversation_history
    try:
        # with open('./src/conversation_history.json', 'r') as file:
        #     conversation_history = json.load(file)
        #     for entry in conversation_history:
        #         chat_window.insert(tk.END, f"{entry['role']}: {entry['content']}\n")
        with open('./src/conversation_history.json', 'r') as file:
            conversation_history = json.load(file)
        with open('./src/now_conversation.json', 'r') as file:
            now_conversation = json.load(file)
            for entry in now_conversation:
                chat_window.insert(tk.END, f"{entry['role']}: {entry['content']}\n")
    except FileNotFoundError:
        conversation_history = []


# 在每次有新對話後保存記錄
def save_conversation_history():
    with open('./src/conversation_history.json', 'w') as file:
        json.dump(conversation_history, file)
    with open('./src/now_conversation.json', 'w') as file:
        json.dump(now_conversation, file)

def analyze_image(image_path):
    """使用 Google Cloud Vision API 分析圖片，並返回描述。"""
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        # 使用 Vision API 進行標籤檢測
        response = client.label_detection(image=image)
        labels = response.label_annotations

        # 將標籤轉換為描述
        description = ', '.join([label.description for label in labels])
        return description
    except Exception as e:
        return f"圖片分析失敗: {e}"

# 新增一個列表來存儲所有圖片的引用
image_references = []

def upload_and_analyze_image():
    """上傳圖片，並使用 Google Cloud Vision 進行辨識。"""
    uploaded_image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.gif")])
    if uploaded_image_path:
        # 先顯示圖片在聊天窗口
        img = Image.open(uploaded_image_path).resize((100, 100))
        img_tk = ImageTk.PhotoImage(img)
        chat_window.image_create(tk.END, image=img_tk)  # 在聊天框中顯示圖片
        chat_window.insert(tk.END, "\n")  # 確保圖片和文字分開
        
        # 將圖片添加到 image_references 列表中以防被垃圾回收
        image_references.append(img_tk)
        
        # 然後使用 Google Cloud Vision API 分析圖片
        description = analyze_image(uploaded_image_path)
        
        # 在聊天窗口中顯示圖片的描述
        chat_window.insert(tk.END, f"圖片描述: {description}\n")

async def fetch_response(session, prompt):
    try:
        async with session.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            },
            json={
                'model': 'gpt-4o',
                'messages': [
                    {'role': 'system', 'content': '你是羅技娘，作為logitech公司的產品小助手，幫助使用者日常生活提醒與規劃。根據使用者的輸入，你需要決定是否生成一張圖片。如果需要生成圖片，請返回 "生成圖片"，否則只需提供文本回應。'},
                ] + [{'role': entry['role'], 'content': entry['content']} for entry in conversation_history],
                'temperature': 0.5,
                'max_tokens': 300,
                'functions': [
                    {
                        "name": "get_weather",
                        "description": "Retrieve the current weather for a given city.",
                        "strict": False,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "city": {
                                    "type": "string",
                                    "description": "The city to get weather for."
                                }
                            },
                            "required": [
                                "city"
                            ]
                        }
                    },
                    {
                        "name": "get_weather_forecast",
                        "description": "Retrieve a 5-day weather forecast for a given city.",
                        "strict": False,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "city": {
                                    "type": "string",
                                    "description": "The city to get a weather forecast for."
                            }
                            },
                            "required": [
                                "city"
                            ]
                        }
                    },
                    {
                        "name": "delete_memory",
                        "description": "user wanna delete the chatting memory",
                        "strict": False,
                        "parameters": {}
                    }
        
                ],
            }
        ) as response:
            try:
                result = await response.json()
                return result
            except Exception as e:
                return {"error": f"Failed to parse JSON: {e}"}
    except Exception as e:
        print(f"API 請求錯誤: {e}")
        return {"error": str(e)}

def get_response(prompt):
    try:

        if not prompt.strip():
            return {"error": "用戶輸入為空，請輸入有效內容。"}
        
        # 將用戶的輸入加入對話歷史
        conversation_history.append({'role': 'user', 'content': prompt})
        now_conversation.append({'role': 'user', 'content': prompt})
        save_conversation_history()

        async def run_fetch():
            async with aiohttp.ClientSession() as session:
                return await fetch_response(session, prompt)

        # 執行非同步函數
        response = asyncio.run(run_fetch())
        # debug
        print("完整回應:", response)

        # 檢查回應中的 function_call
        if 'choices' in response and 'function_call' in response['choices'][0]['message']:
            function_call = response['choices'][0]['message']['function_call']
            if function_call['name'] == 'get_weather':
                city = json.loads(function_call['arguments'])['city']
                weather_info = weather_service.get_weather(city)
                return f"羅技娘偷偷告訴你：{weather_info} ><"  # 返回天氣資訊
            elif function_call['name'] == 'get_weather_forecast':
                city = json.loads(function_call['arguments'])['city']
                forecast_info = weather_service.get_weather_forecast(city)
                return f"羅技娘偷偷告訴你：{forecast_info} ><"  # 返回天氣預報
            elif function_call['name'] == 'delete_memory':
                delete_memory()  # 呼叫刪除函數
                return "所有聊天紀錄已刪除。"
        else:
            # 返回正常的聊天回應
            return response['choices'][0]['message']['content']

    except Exception as e:
        print(f"Error fetching response: {e}")
        return {"error": str(e)}

def delete_memory():
    """刪除聊天紀錄的 JSON 檔案。"""
    try:
        if os.path.exists('./src/now_conversation.json'):
            os.remove('./src/now_conversation.json')
            global now_conversation
            now_conversation = []  # 清空內存中的對話歷史
            print("聊天紀錄已成功刪除。")
            # 清空聊天視窗中的內容
            chat_window.config(state=tk.NORMAL)  # 解鎖聊天窗口使其可編輯
            chat_window.delete(1.0, tk.END)  # 刪除視窗中所有文字
            chat_window.config(state=tk.DISABLED)  # 再次將聊天窗口設為不可編輯
        else:
            print("沒有發現聊天紀錄檔案。")
    except Exception as e:
        print(f"刪除聊天紀錄時出現錯誤: {e}")

def generate_image(prompt):

    response = requests.post(
        'https://api.openai.com/v1/images/generations',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        json={
            'prompt': prompt,
            'n': 1,
            'size': '1024x1024'
        }
    )
    
    if response.status_code == 200:
        image_url = response.json()['data'][0]['url']
        image_data = requests.get(image_url).content
        return Image.open(BytesIO(image_data))
    else:
        print(f"圖片生成失敗，狀態碼: {response.status_code}, 回應: {response.text}")
        return None

engine = pyttsx3.init()
def speak(text):
    engine.setProperty('rate', 200)  # 設定語速
    engine.setProperty('volume', 1)  # 設定音量
    
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'female' in voice.name.lower():  # 選擇女性聲音
            engine.setProperty('voice', voice.id)
            break
    
    engine.say(text)
    engine.runAndWait()
    

# 使用 threading 讓語音播放在背景執行
def speak_async(text):
    global speak_thread
    speak_thread = threading.Thread(target=speak, args=(text,))
    speak_thread.start()    

def open_input_dialog():
    """彈出一個對話框來讓用戶輸入文本"""
    prompt = simpledialog.askstring("輸入提示", "請輸入您的Prompt:")
    if prompt:
        send_message(prompt)  # 使用者輸入的內容會被傳遞到 send_message 函數

def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("請開始說話...")
        audio = recognizer.listen(source)

    try:
        user_input = recognizer.recognize_google(audio, language='zh-TW')
        chat_window.insert(tk.END, f"You: {user_input}\n")
        send_message(user_input)
    except sr.UnknownValueError:
        chat_window.insert(tk.END, "GPT: 語音識別失敗，請再試一次。\n\n")
    except sr.RequestError as e:
        chat_window.insert(tk.END, f"GPT: 無法連接到語音識別服務; {e}\n\n")

def on_closing():
    """當關閉應用程式時，停止所有語音播放並正確退出。"""
    global speak_thread  # 追踪語音播放的執行緒
    engine.stop()  # 停止 pyttsx3 引擎
    if speak_thread.is_alive():  # 檢查語音播放的執行緒是否仍在運行
        speak_thread.join(timeout=1)  # 等待執行緒結束
    root.quit()  # 結束主循環
    root.destroy()  # 關閉應用程式視窗


def process_response(response):
    # 如果 response 是字典且有 'choices' 欄位，處理 GPT 回應
    if isinstance(response, dict) and 'choices' in response and len(response['choices']) > 0:
        message_content = response['choices'][0]['message']['content']
        return message_content
    # 如果 response 是字串，直接返回它
    elif isinstance(response, str):
        return response
    # 如果 response 不符合預期，返回錯誤提示
    else:
        return "GPT: 錯誤：回應不正確或缺少 'choices' 欄位。"

def send_message(user_input):
    if user_input:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, f"You: {user_input}\n")
        chat_window.config(state=tk.DISABLED)
        
        entry.delete(0, tk.END)

        # 獲取 API 回應
        response = get_response(user_input)

        # 打印 response 進行調試
        print("Response received:", response)

        # 處理 response 回應
        message_content = process_response(response)
        
        # 顯示 GPT 回應
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, f"GPT: {message_content}\n\n")
        chat_window.config(state=tk.DISABLED)

        # 將 GPT 回覆保存到記憶變量
        conversation_history.append({'role': 'assistant', 'content': message_content})
        now_conversation.append({'role': 'user', 'content': user_input})
        
        # 儲存到文件
        save_conversation_history()
        speak_async(message_content)

        # 檢查是否包含生成圖片的指令
        if "生成圖片" in message_content:
            print(f"生成圖片指令觸發，prompt為: {user_input}")
            image = generate_image(user_input)
            if image:
                display_image(image)
            else:
                chat_window.config(state=tk.NORMAL)
                chat_window.insert(tk.END, "GPT: 無法生成圖片，請稍後再試。\n\n")
                chat_window.config(state=tk.DISABLED)


def display_image(image):
    global generated_image, image_reference  # 儲存圖片的引用
    img = image.resize((250, 250))
    img_tk = ImageTk.PhotoImage(img)

    chat_window.image_create(tk.END, image=img_tk)
    chat_window.insert(tk.END, "\n")

    generated_image = image  # 保存生成的圖片
    image_reference = img_tk  # 保存圖片引用，防止被垃圾回收

def download_image():
    global generated_image
    if generated_image is not None:
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if save_path:
            try:
                generated_image.save(save_path)
                messagebox.showinfo("成功", "圖片已成功保存！")
            except Exception as e:
                messagebox.showerror("錯誤", f"無法保存圖片：{e}")
    else:
        messagebox.showwarning("警告", "目前沒有生成的圖片可供下載。")

def initial_message():
    initial_prompt = "我使用的是 gpt-4o 模型，我是羅技娘～，請問有什麼我可以幫忙的？"
    chat_window.insert(tk.END, f"GPT: {initial_prompt}\n\n")
    speak_async(initial_prompt)

# 新增功能：綁定按鍵
def bind_keys():
    root.bind('<i>', lambda event: open_input_dialog())  # 按下I鍵
    root.bind('<u>', lambda event: upload_and_analyze_image())  # 按下U鍵
    root.bind('<s>', lambda event: download_image())  # 按下S鍵
    root.bind('<r>', lambda event: record_audio())  # 按下S鍵


def show_next_hint():
    global current_hint_index
    current_hint_index = (current_hint_index + 1) % len(hints)  # 切換到下一頁
    hint_text.set(hints[current_hint_index])  # 更新提示框中的文字

if __name__ == "__main__":
    # 提示框的頁面內容
    hints = [
        "press 'u' to upload file\npress 'd' to download file",
        "pree 'i' to text message\npress 'r' to record sound。",
        "這是提示頁面 3 的內容。"
    ]
    # 當前頁面的索引
    current_hint_index = 0
    
    root = tk.Tk()
    root.title("Chat with GPT")
    # 設定視窗背景顏色
    root.configure(bg="white")

    # 設置視窗為最上方
    root.attributes('-topmost', True)

    # 使用 grid 佈局
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    # 添加 Vpet 在最左側
    vpet_viewer = Vpet(root, "./src/vpet.gif")
    vpet_viewer.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

    # 添加滾動條
    scrollbar = tk.Scrollbar(root)
    scrollbar.grid(row=0, column=2, sticky="ns")

    # 建立聊天窗口並綁定滾動條
    chat_window = tk.Text(root, bd=1, bg="white", fg="black", width=50, height=8, yscrollcommand=scrollbar.set)
    chat_window.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    scrollbar.config(command=chat_window.yview)

    # 建立用戶輸入框
    entry = tk.Entry(root, bd=1, bg="white", fg="black", insertbackground="black")
    entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

    # 綁定回車鍵以發送消息
    entry.bind("<Return>", lambda event: send_message(entry.get()))

    # 建立按鈕樣式，讓按鈕有圓滑和艷色
    button_style = {
        "bg": "#e6e6e6",
        "fg": "black",
        "activebackground": "#d1d1d1",
        "cursor": "hand2",
        "activeforeground": "black",
        "bd": 0,
        "highlightthickness": 0
    }

    # 將所有按鈕放在同一行
    button_frame = tk.Frame(root, bg="white")  # 新增框架以容納按鈕
    button_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")  # 按鈕框架位置

    # 建立發送按鈕
    send_button = tk.Button(button_frame, text="Send", **button_style, command=lambda: send_message(entry.get()))
    send_button.grid(row=0, column=0, padx=5, pady=5)

    # 建立錄音按鈕
    record_button = tk.Button(button_frame, text="錄音", **button_style, command=record_audio)
    record_button.grid(row=0, column=1, padx=5, pady=5)

    # 上傳圖片按鈕
    upload_button = tk.Button(button_frame, text="上傳圖片", **button_style, command=upload_and_analyze_image)
    upload_button.grid(row=0, column=2, padx=5, pady=5)

    # 下載圖片按鈕
    download_button = tk.Button(button_frame, text="下載圖片", **button_style, command=download_image)
    download_button.grid(row=0, column=3, padx=5, pady=5)

    # 左下角提示框
    tutorial_app = TutorialApp(root)

    # update past text
    load_conversation_history()

    # 綁定按鍵
    bind_keys()

    # 顯示初始訊息
    initial_message()

    # 當關閉應用程式時，執行 on_closing
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 開始 GUI 主循環
    root.mainloop()




# 調整滑鼠 DPI，AI 自動查找滑鼠 ID
def adjust_mouse_dpi(dpi_value):
    async def run():
        mouse_id = await find_device_id("mouse")
        if mouse_id:
            print(f"找到滑鼠 ID: {mouse_id}")
            command = {
                "verb": "set",
                "path": "dpi",
                "args": {
                    "unitId": mouse_id,
                    "value": dpi_value
                }
            }
            await logidevmon.send_ws_msg(command)
        else:
            print("未找到滑鼠")
    
    asyncio.run(run())



# unused


# {
#     'functions': [
#         {
#             "name": "adjust_mouse_dpi",
#             "description": "Adjust the DPI setting of the mouse.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "device_id": {"type": "integer", "description": "The ID of the mouse device."},
#                     "dpi_value": {"type": "integer", "description": "The desired DPI value."}
#                 },
#                 "required": ["device_id", "dpi_value"]
#             }
#         },
#         {
#             "name": "set_keyboard_shortcut",
#             "description": "Set a keyboard shortcut on the Logitech device.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "device_id": {"type": "integer", "description": "The ID of the keyboard device."},
#                     "key": {"type": "string", "description": "The key to bind."},
#                     "action": {"type": "string", "description": "The action to bind to the key."}
#                 },
#                 "required": ["device_id", "key", "action"]
#             }
#         }
#     ]
# }


# # 調整滑鼠 DPI，AI 自動查找滑鼠 ID
# def adjust_mouse_dpi(dpi_value):
#     async def run():
#         mouse_id = await find_device_id("mouse")
#         if mouse_id:
#             print(f"找到滑鼠 ID: {mouse_id}")
#             command = {
#                 "verb": "set",
#                 "path": "dpi",
#                 "args": {
#                     "unitId": mouse_id,
#                     "value": dpi_value
#                 }
#             }
#             await logidevmon.send_ws_msg(command)
#         else:
#             print("未找到滑鼠")
    
#     asyncio.run(run())

# # 設定鍵盤快捷鍵，AI 自動查找鍵盤 ID
# def set_keyboard_shortcut(key, action):
#     async def run():
#         keyboard_id = await find_device_id("keyboard")
#         if keyboard_id:
#             print(f"找到鍵盤 ID: {keyboard_id}")
#             command = {
#                 "verb": "set",
#                 "path": "specialKeyConfig",
#                 "args": {
#                     "unitId": keyboard_id,
#                     "controlId": key,
#                     "action": action
#                 }
#             }
#             await logidevmon.send_ws_msg(command)
#         else:
#             print("未找到鍵盤")
    
#     asyncio.run(run())

# # 檢查裝置狀態
# def check_device_status(device_type):
#     async def run():
#         device_id = await find_device_id(device_type)
#         if device_id:
#             command = {
#                 "verb": "get",
#                 "path": "device",
#                 "args": {
#                     "unitId": device_id
#                 }
#             }
#             device_status = await logidevmon.send_ws_msg(command)
#             print(f"{device_type.capitalize()} 狀態: {device_status}")
#         else:
#             print(f"未找到 {device_type}")
    
#     asyncio.run(run())


# # 設定鍵盤快捷鍵，AI 自動查找鍵盤 ID
# def set_keyboard_shortcut(key, action):
#     async def run():
#         keyboard_id = await find_device_id("keyboard")
#         if keyboard_id:
#             print(f"找到鍵盤 ID: {keyboard_id}")
#             command = {
#                 "verb": "set",
#                 "path": "specialKeyConfig",
#                 "args": {
#                     "unitId": keyboard_id,
#                     "controlId": key,
#                     "action": action
#                 }
#             }
#             await logidevmon.send_ws_msg(command)
#         else:
#             print("未找到鍵盤")
    
#     asyncio.run(run())

# # 檢查裝置狀態
# def check_device_status(device_type):
#     async def run():
#         device_id = await find_device_id(device_type)
#         if device_id:
#             command = {
#                 "verb": "get",
#                 "path": "device",
#                 "args": {
#                     "unitId": device_id
#                 }
#             }
#             device_status = await logidevmon.send_ws_msg(command)
#             print(f"{device_type.capitalize()} 狀態: {device_status}")
#         else:
#             print(f"未找到 {device_type}")
    
#     asyncio.run(run())

# async def find_device_id(device_type):
#     command = {
#         "verb": "get",
#         "path": "devices"
#     }
#     devices = await logidevmon.send_ws_msg(command)
    
#     for device in devices.get("value", []):
#         if device["type"] == device_type:  # 根據裝置類型來篩選 (例如 'mouse' 或 'keyboard')
#             return device["unitId"]
#     return None
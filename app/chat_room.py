import tkinter as tk
from tkinter import ttk
import requests
from PIL import Image, ImageTk
from io import BytesIO
import pyttsx3
import speech_recognition as sr
import asyncio
import aiohttp
import threading
import os
from google.cloud import vision
from tkinter import filedialog, messagebox
from vpet import Vpet
import json

# 設定 Google Cloud Vision API 憑證
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './src/silver-theme-439105-i6-ac61c12c257b.json'
client = vision.ImageAnnotatorClient()

# 儲存生成的圖片以便下載
generated_image = None

# memory recorder
conversation_history = []


# 在聊天開始時加載之前的對話記錄
import os
import json

def load_conversation_history():
    global conversation_history
    if os.path.exists('conversation_history.json'):
        try:
            with open('./src/conversation_history.json', 'r') as file:
                # 檢查檔案是否有內容
                if os.path.getsize('conversation_history.json') > 0:
                    conversation_history = json.load(file)
                    for entry in conversation_history:
                        chat_window.insert(tk.END, f"{entry['role']}: {entry['content']}\n")
                else:
                    conversation_history = []
        except json.JSONDecodeError:
            # 如果檔案無法解析，初始化空對話歷史
            conversation_history = []
    else:
        conversation_history = []

# 在每次有新對話後保存記錄
def save_conversation_history():
    with open('./src/conversation_history.json', 'w') as file:
        json.dump(conversation_history, file)

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



# 你的 OpenAI API Key
api_key = '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'

async def fetch_response(session, prompt):
    async with session.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        json={
            'model': 'gpt-4o',
            'messages': conversation_history,
            'temperature': 0.5,
            'max_tokens': 300
        }
    ) as response:
        if response.status == 200:
            return await response.json()
        else:
            return {"error": f"Error: {response.status}"}

def get_response(prompt):
    try:
        # 將用戶的輸入加入對話歷史
        conversation_history.append({'role': 'user', 'content': prompt})
        save_conversation_history()

        async def run_fetch():
            async with aiohttp.ClientSession() as session:
                return await fetch_response(session, prompt)

        return asyncio.run(run_fetch())
    except Exception as e:
        print(f"Error fetching response: {e}")
        return {"error": str(e)}

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
        return None

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1)
    
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'female' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    
    engine.say(text)
    engine.runAndWait()

# 使用 threading 讓語音播放在背景執行
def speak_async(text):
    threading.Thread(target=speak, args=(text,)).start()

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

def send_message(user_input):
    if user_input:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, f"You: {user_input}\n")
        chat_window.config(state=tk.DISABLED)
        
        entry.delete(0, tk.END)

        response = get_response(user_input)

        if 'error' in response:
            chat_window.config(state=tk.NORMAL)
            chat_window.insert(tk.END, f"GPT: 錯誤：{response['error']}\n\n")
            chat_window.config(state=tk.DISABLED)
            return

        if 'choices' in response and len(response['choices']) > 0:
            message_content = response['choices'][0]['message']['content']
            chat_window.config(state=tk.NORMAL)
            chat_window.insert(tk.END, f"GPT: {message_content}\n\n")
            chat_window.config(state=tk.DISABLED)

            # 將 GPT 回覆保存到記憶變量
            conversation_history.append({'role': 'assistant', 'content': message_content})

            # 儲存到文件
            save_conversation_history()
            speak_async(message_content)

            if "生成圖片" in message_content:
                image = generate_image(user_input)
                if image:
                    display_image(image)
                else:
                    chat_window.config(state=tk.NORMAL)
                    chat_window.insert(tk.END, "GPT: 無法生成圖片，請稍後再試。\n\n")
                    chat_window.config(state=tk.DISABLED)
        else:
            chat_window.config(state=tk.NORMAL)
            chat_window.insert(tk.END, "GPT: 錯誤：未獲得有效的回應。\n\n")
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

if __name__ == "__main__":
    
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

    # update past text
    load_conversation_history()

    # 顯示初始訊息
    initial_message()

    # 開始 GUI 主循環
    root.mainloop()
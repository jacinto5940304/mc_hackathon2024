import tkinter as tk
import requests
from PIL import Image, ImageTk
from io import BytesIO

# 你的 OpenAI API Key
api_key = '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'

def get_response(prompt):
    # 判斷用戶是否要求生成圖片
    if "畫" in prompt or "圖片" in prompt:
        return generate_image(prompt)
    else:
        # 發送 API 請求並返回結果
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            },
            json={
                'model': 'gpt-4o',  # 確保使用正確的模型
                'messages': [
                    {'role': 'system', 'content': '你是羅技娘，作為logitech公司的產品小助手，幫助使用者日常生活提醒與規劃.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.4,
                'max_tokens': 300
            }
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error: {response.status_code}"

def generate_image(prompt):
    # 發送請求給OpenAI的DALL·E API
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

def send_message(event=None):
    # 從用戶輸入獲取文本並顯示回應
    user_input = entry.get()
    if user_input:
        chat_window.insert(tk.END, f"You: {user_input}\n")
        entry.delete(0, tk.END)
        
        if "畫" in user_input or "圖片" in user_input:
            image = get_response(user_input)
            if image:
                display_image(image)
            else:
                chat_window.insert(tk.END, f"GPT: 無法生成圖片，請稍後再試。\n\n")
        else:
            response = get_response(user_input)
            chat_window.insert(tk.END, f"GPT: {response}\n\n")

def display_image(image):
    # 將圖片顯示在Tkinter界面
    img = image.resize((250, 250))  # 調整圖片大小以適應窗口
    img_tk = ImageTk.PhotoImage(img)
    
    image_label.config(image=img_tk)
    image_label.image = img_tk  # 保持對象的引用，防止垃圾回收

def initial_message():
    # 初始啟動時的訊息，顯示模型和助手身份
    initial_prompt = "我使用的是 gpt-4o 模型，我是羅技娘～，請問有什麼我可以幫忙的？"
    chat_window.insert(tk.END, f"GPT: {initial_prompt}\n\n")

# 建立視窗
root = tk.Tk()
root.title("Chat with GPT")

# 建立聊天窗口
chat_window = tk.Text(root, bd=1, bg="white", width=50, height=8)
chat_window.pack(padx=10, pady=10)

# 建立用戶輸入框
entry = tk.Entry(root, bd=1, bg="white", width=50)
entry.pack(padx=10, pady=10)

# 綁定 Enter 鍵事件到 Entry 輸入框
entry.bind("<Return>", send_message)

# 建立發送按鈕
send_button = tk.Button(root, text="Send", width=10, command=send_message)
send_button.pack(pady=10)

# 顯示圖片的Label
image_label = tk.Label(root)
image_label.pack(padx=10, pady=10)

# 顯示初始訊息
initial_message()

# 開始 GUI 主循環
root.mainloop()

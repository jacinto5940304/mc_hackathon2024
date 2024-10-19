import tkinter as tk
import requests

# 你的 OpenAI API Key
api_key = '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'

def get_response(prompt):
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
                {'role': 'system', 'content': 'You are a helpful assistant.'},
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

def send_message(event=None):
    # 從用戶輸入獲取文本並顯示回應
    user_input = entry.get()
    if user_input:
        chat_window.insert(tk.END, f"You: {user_input}\n")
        entry.delete(0, tk.END)
        response = get_response(user_input)
        chat_window.insert(tk.END, f"GPT: {response}\n\n")

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

# 開始 GUI 主循環
root.mainloop()
import tkinter as tk
import openai

# 你的 OpenAI API Key
openai.api_key = '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'

def get_response(prompt):
    # 使用 GPT-4 與 OpenAI 進行聊天
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=128,
        temperature=0.5
    )
    return response["choices"][0]["message"]["content"]

def send_message():
    # 從用戶輸入框獲取文本，並在聊天視窗顯示
    user_input = entry.get()
    if user_input:
        chat_window.insert(tk.END, f"You: {user_input}\n")
        entry.delete(0, tk.END)
        
        # 獲取 GPT 的回應
        response = get_response(user_input)
        chat_window.insert(tk.END, f"GPT: {response}\n\n")

# 建立視窗
root = tk.Tk()
root.title("Chat with GPT-4o")

# 建立聊天窗口
chat_window = tk.Text(root, bd=1, bg="white", width=50, height=20)
chat_window.pack(padx=10, pady=10)

# 建立用戶輸入框
entry = tk.Entry(root, bd=1, bg="white", width=50)
entry.pack(padx=10, pady=10)

# 建立發送按鈕
send_button = tk.Button(root, text="Send", width=10, command=send_message)
send_button.pack(pady=10)

# 開始 GUI 主循環
root.mainloop()
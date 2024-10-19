import tkinter as tk
import requests
import json

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatGPT Dialog")

        # 創建文本區域顯示聊天記錄
        self.text_area = tk.Text(self.root, height=20, width=60, state=tk.DISABLED)
        self.text_area.pack(pady=10)

        # 創建輸入框
        self.entry_field = tk.Entry(self.root, width=50)
        self.entry_field.pack(side=tk.LEFT, padx=10, pady=10)

        # 創建發送按鈕
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # 設置 OpenAI API Key
        self.api_key = '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'  # 請替換為你自己的 API Key

    # 發送訊息函數
    def send_message(self):
        user_input = self.entry_field.get()
        if user_input:
            self.update_chat("You", user_input)  # 顯示用戶輸入的訊息
            self.entry_field.delete(0, tk.END)   # 清除輸入框
            self.get_response(user_input)        # 獲取 ChatGPT 的回應

    # 更新聊天記錄顯示
    def update_chat(self, sender, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{sender}: {message}\n")
        self.text_area.config(state=tk.DISABLED)

    # 獲取 ChatGPT 回應
    def get_response(self, prompt):
        self.update_chat("Assistant", "Generating response...")  # 顯示生成回應中...

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        data = {
            "model": "gpt-3.5-turbo",  # 使用 gpt-3.5-turbo 模型
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            # 發送請求到 OpenAI API 並接收回應
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()

            # 解析 ChatGPT 的回應內容
            chat_response = response_data['choices'][0]['message']['content'].strip()
            self.update_chat("Assistant", chat_response)
        except requests.exceptions.RequestException as e:
            # 處理可能的請求錯誤
            self.update_chat("Error", f"Failed to get response: {str(e)}")

# 創建 Tkinter 視窗
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
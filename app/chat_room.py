import tkinter as tk
import openai
import os

# 初始化 OpenAI 客戶端
openai.api_key = os.getenv('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')  # 設定你的 API 金鑰

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chatting Room")

        # 創建文本區域顯示聊天記錄
        self.text_area = tk.Text(self.root, height=20, width=60, state=tk.DISABLED)
        self.text_area.pack(pady=10)

        # 創建輸入框
        self.entry_field = tk.Entry(self.root, width=50)
        self.entry_field.pack(side=tk.LEFT, padx=10, pady=10)

        # 創建發送按鈕
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=10)

    # 發送訊息函數
    def send_message(self):
        user_input = self.entry_field.get()
        if user_input:
            self.update_chat("You", user_input)  # 顯示用戶輸入的訊息
            self.entry_field.delete(0, tk.END)   # 清除輸入框
            gpt_assistant_prompt = "You are a helpful assistant."  # 固定助手身份
            self.get_response(gpt_assistant_prompt, user_input)  # 獲取 ChatGPT 的回應

    # 更新聊天記錄顯示
    def update_chat(self, sender, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{sender}: {message}\n")
        self.text_area.config(state=tk.DISABLED)

    # 獲取 ChatGPT 回應
    def get_response(self, gpt_assistant_prompt, gpt_user_prompt):
        self.update_chat("Assistant", "Generating response...")  # 顯示生成回應中...

        try:
            # 使用新的 OpenAI API 調用
            response = openai.completions.create(
                model="gpt-4",  # 使用 GPT-4 模型
                messages=[
                    {"role": "system", "content": gpt_assistant_prompt},
                    {"role": "user", "content": gpt_user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
                frequency_penalty=0.0
            )

            # 解析回應
            chat_response = response['choices'][0]['message']['content'].strip()
            self.update_chat("Assistant", chat_response)

        except Exception as e:
            # 捕捉所有可能的錯誤，並打印錯誤信息
            self.update_chat("Error", f"Failed to get response: {str(e)}")

# 創建 Tkinter 視窗
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
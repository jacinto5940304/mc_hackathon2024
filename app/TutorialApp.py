import datetime
import tkinter as tk


class TutorialApp:
    def __init__(self, parent):
        self.page = 1
        self.parent = parent
        self.create_tutorial_frame()

    def create_tutorial_frame(self):
        self.frame = tk.Frame(self.parent, bg="white", width=300, height=100)
        self.frame.grid(row=3, column=0, columnspan=2, sticky="sw")

        self.label = tk.Label(self.frame, text=f"這是提示頁面 {self.page} 的內容。")
        self.label.grid(row=0, column=0, padx=10, pady=10)

        self.next_button = tk.Button(self.frame, text="下一頁", command=self.next_page)
        self.next_button.grid(row=0, column=1, padx=10, pady=10)

    def next_page(self):
        self.page += 1
        self.update_content()

    def update_content(self):
        if self.page == 1:
            self.label.config(text="'u': upload; 'd': download")
        elif self.page == 2:
            self.label.config(text="'i': text, 'r': record''")
        elif self.page == 3:
            self.show_ai_reminder()
            self.next_button.grid_remove()  # 隱藏按鈕

    def show_ai_reminder(self):
        # 取得當前日期和時間
        now = datetime.datetime.now()
        hour = now.hour

        # 根據時間提供不同的提示
        if hour < 12:
            reminder = "早上好！別忘了檢查今天的任務。"
        elif 12 <= hour < 18:
            reminder = "下午好！記得處理下午的工作事項。"
        else:
            reminder = "晚上好！該放鬆一下，準備迎接明天。"

        current_time = now.strftime("%Y-%m-%d %H:%M:%S")

        # 更新頁面內容

        self.label.config(text=f"\n羅技娘 提示: {reminder}\n當前時間是：{current_time}")

        # 每1000毫秒 (1秒) 更新一次時間
        self.parent.after(1000, self.show_ai_reminder)


# 主應用程式
if __name__ == "__main__":
    root = tk.Tk()
  

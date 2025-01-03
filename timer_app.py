import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime, timedelta
import threading
import time
import subprocess

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("定时关机助手")
        self.root.geometry("300x350")  # 减小窗口高度
        
        # 创建主框架并居中
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(expand=True, fill='both')
        
        # 标题
        title_label = ttk.Label(self.main_frame, text="定时关机助手", 
                              font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 选择操作类型
        action_frame = ttk.LabelFrame(self.main_frame, text="选择操作", padding="10")
        action_frame.pack(fill='x', pady=(0, 10))
        
        self.action_var = tk.StringVar(value="sleep")
        actions = [
            ("睡眠", "sleep"),
            ("休眠", "hibernate"),
            ("关机", "shutdown")
        ]
        
        radio_frame = ttk.Frame(action_frame)
        radio_frame.pack()
        for i, (text, value) in enumerate(actions):
            ttk.Radiobutton(radio_frame, text=text, value=value, 
                          variable=self.action_var).grid(row=0, column=i, padx=20)
        
        # 时间输入框架
        time_frame = ttk.LabelFrame(self.main_frame, text="时间设置", padding="10")
        time_frame.pack(fill='x', pady=(0, 10))
        
        time_input_frame = ttk.Frame(time_frame)
        time_input_frame.pack()
        ttk.Label(time_input_frame, text="设置时间:").grid(row=0, column=0, padx=5)
        self.time_var = tk.StringVar(value="2")
        self.time_entry = ttk.Entry(time_input_frame, textvariable=self.time_var, width=10)
        self.time_entry.grid(row=0, column=1, padx=5)
        ttk.Label(time_input_frame, text="分钟").grid(row=0, column=2, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始计时", 
                                     command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=10)
        
        self.cancel_button = ttk.Button(button_frame, text="取消计时", 
                                      command=self.cancel_timer, state='disabled')
        self.cancel_button.grid(row=0, column=1, padx=10)
        
        # 倒计时显示
        self.countdown_var = tk.StringVar(value="计时已取消")
        countdown_label = ttk.Label(self.main_frame, textvariable=self.countdown_var,
                                  font=("微软雅黑", 12))
        countdown_label.pack(pady=10)
        
        # 状态显示
        self.status_var = tk.StringVar(value="")
        status_label = ttk.Label(self.main_frame, textvariable=self.status_var,
                               font=("微软雅黑", 10))
        status_label.pack(pady=5)
        
        self.timer_active = False
        self.countdown_thread = None
        
        # 设置样式
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("TLabelframe", padding=5)
    
    def update_countdown(self, end_time):
        """更新倒计时显示"""
        while self.timer_active:
            current_time = datetime.now()
            remaining = end_time - current_time
            
            if remaining.total_seconds() <= 0:
                break
            
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            countdown_text = f"剩余时间: {hours:02d}:{minutes:02d}:{seconds:02d}"
            self.root.after(0, lambda t=countdown_text: self.countdown_var.set(t))
            
            time.sleep(1)
        
        if self.timer_active:  # 如果是正常结束（非取消）
            self.execute_final_command()
        
        # 恢复界面状态
        self.root.after(0, self.reset_ui_state)
    
    def reset_ui_state(self):
        """重置界面状态"""
        self.timer_active = False
        self.start_button.configure(state='normal')
        self.cancel_button.configure(state='disabled')
        self.countdown_var.set("计时已取消")
        self.status_var.set("")
    
    def execute_final_command(self):
        """执行最终的系统命令"""
        action = self.action_var.get()
        if action == "shutdown":
            subprocess.run(["shutdown", "/s", "/t", "0"], shell=True)
        elif action == "sleep":
            subprocess.run(["powercfg", "/hibernate", "off"], shell=True)
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], shell=True)
        elif action == "hibernate":
            subprocess.run(["shutdown", "/h"], shell=True)
    
    def start_timer(self):
        try:
            minutes = int(self.time_var.get())
            if minutes <= 0:
                raise ValueError("时间必须大于0")
            
            # 重置状态
            self.timer_active = True
            
            # 更新按钮状态
            self.start_button.configure(state='disabled')
            self.cancel_button.configure(state='normal')
            
            # 计算结束时间
            end_time = datetime.now() + timedelta(minutes=minutes)
            self.status_var.set(f"将在 {end_time.strftime('%H:%M:%S')} 执行操作")
            
            # 启动倒计时线程
            if self.countdown_thread is not None and self.countdown_thread.is_alive():
                self.timer_active = False
                self.countdown_thread.join()
            
            self.countdown_thread = threading.Thread(
                target=self.update_countdown, args=(end_time,))
            self.countdown_thread.daemon = True
            self.countdown_thread.start()
            
        except ValueError as e:
            messagebox.showerror("错误", str(e))
    
    def cancel_timer(self):
        if self.timer_active:
            # 先停止倒计时
            self.timer_active = False
            
            # 取消系统命令
            action = self.action_var.get()
            if action == "shutdown":
                try:
                    subprocess.run(["shutdown", "/a"], shell=True)
                except subprocess.CalledProcessError:
                    pass  # 忽略错误，因为可能没有待取消的关机命令
            
            # 终止所有timeout进程
            try:
                subprocess.run(["taskkill", "/f", "/im", "timeout.exe"], 
                             shell=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                pass
            
            # 重置界面状态
            self.reset_ui_state()
        else:
            self.status_var.set("没有正在进行的计时")

if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop() 
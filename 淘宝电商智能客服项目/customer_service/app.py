import sys
import os
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from openai import OpenAI
import difflib

# 设置API密钥和基础URL
client = OpenAI(
    api_key="输入您deepseek的API密钥",
    base_url="https://api.deepseek.com/v1"
)

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能客服系统 - 您的贴心助手")
        self.root.geometry("1000x700")
        
        # 设置主题颜色
        self.colors = {
            "primary": "#FF4400",  # 淘宝红
            "secondary": "#FFF2E8",  # 浅橙色背景
            "text": "#404040",  # 深灰色文字
            "border": "#E8E8E8"  # 边框颜色
        }
        
        # 加载知识库
        self.load_knowledge_base()
        
        # 初始化消息历史
        self.messages = []
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建标题栏
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame,
            text="智能客服中心",
            font=("微软雅黑", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # 添加退出按钮到标题栏
        style = ttk.Style()
        style.configure(
            "Send.TButton",
            padding=10,
            font=("微软雅黑", 10)
        )
        
        self.exit_btn = ttk.Button(
            title_frame,
            text="退出",
            command=self.confirm_exit,
            style="Send.TButton"
        )
        self.exit_btn.pack(side=tk.RIGHT)
        
        # 聊天显示区域
        chat_frame = ttk.Frame(self.main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            bg="white"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=5)
        self.chat_display.config(state=tk.DISABLED)
        
        # 输入区域框架
        input_outer_frame = ttk.Frame(self.main_frame)
        input_outer_frame.pack(fill=tk.X, pady=10)
        
        # 输入框架
        input_frame = ttk.Frame(input_outer_frame)
        input_frame.pack(fill=tk.X)
        
        # 输入区域
        self.input_box = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            height=4,
            font=("微软雅黑", 10)
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(input_outer_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 发送按钮
        self.send_btn = ttk.Button(
            button_frame,
            text="发送",
            command=self.send_message,
            style="Send.TButton"
        )
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        # 清除按钮
        self.clear_btn = ttk.Button(
            button_frame,
            text="清除对话",
            command=self.clear_chat,
            style="Send.TButton"
        )
        self.clear_btn.pack(side=tk.LEFT)
        
        # 快捷问题框架
        quick_frame = ttk.Frame(self.main_frame)
        quick_frame.pack(fill=tk.X, pady=(10, 0))
        
        quick_label = ttk.Label(
            quick_frame,
            text="常见问题：",
            font=("微软雅黑", 10)
        )
        quick_label.pack(side=tk.LEFT, padx=(0, 10))
        
        quick_questions = [
            "营业时间",
            "退换货政策",
            "支付方式",
            "配送说明",
            "会员优惠"
        ]
        
        for q in quick_questions:
            btn = ttk.Button(
                quick_frame,
                text=q,
                command=lambda x=q: self.quick_question(x),
                style="Send.TButton"
            )
            btn.pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键发送消息
        self.input_box.bind("<Return>", lambda e: self.send_message())
        
        # 绑定关闭窗口事件
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)
        
        # 显示欢迎消息
        self.append_message(
            "系统: 您好！我是您的智能客服助手。请问有什么可以帮您？\n"
            "您可以直接输入问题，或点击下方的常见问题按钮。"
        )
    
    def confirm_exit(self):
        """确认退出对话"""
        if messagebox.askokcancel("确认退出", "确定要结束对话吗？"):
            self.root.quit()
    
    def load_knowledge_base(self):
        try:
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
        except Exception as e:
            self.knowledge_base = {}
    
    def quick_question(self, question):
        """处理快捷问题按钮点击"""
        self.input_box.delete("1.0", tk.END)
        self.input_box.insert("1.0", question)
        self.send_message()
    
    def find_best_match(self, query, choices, threshold=0.6):
        """使用模糊匹配找到最佳匹配"""
        if not choices:
            return None, 0
        
        matches = []
        for choice in choices:
            ratio = difflib.SequenceMatcher(None, query, choice).ratio()
            matches.append((choice, ratio))
        
        best_match = max(matches, key=lambda x: x[1])
        return best_match if best_match[1] >= threshold else (None, 0)
    
    def format_message(self, message, is_user=False):
        """格式化消息显示"""
        prefix = "用户" if is_user else "客服"
        return f"{prefix}: {message}\n"
    
    def find_in_knowledge_base(self, query):
        """在知识库中查找匹配的回答"""
        if not self.knowledge_base:
            return None, None
        
        result = {
            "response": None,
            "source": None,
            "confidence": 0
        }
        
        # 在常见问题中搜索
        questions = [qa["question"] for qa in self.knowledge_base.get("常见问题", [])]
        best_question, ratio = self.find_best_match(query, questions)
        
        if best_question and ratio > result["confidence"]:
            for qa in self.knowledge_base["常见问题"]:
                if qa["question"] == best_question:
                    result = {
                        "response": qa["answer"],
                        "source": "常见问题",
                        "confidence": ratio
                    }
        
        # 在产品信息中搜索
        product_names = []
        for category in self.knowledge_base.get("产品信息", []):
            for product in category["products"]:
                product_names.append(product["name"])
                # 精确匹配
                if query in product["name"] or query in product["description"]:
                    return (f"产品名称：{product['name']}\n"
                           f"描述：{product['description']}\n"
                           f"价格：{product['price']}\n"
                           f"特点：\n" + "\n".join(f"- {f}" for f in product["features"])), "产品信息"
        
        # 模糊匹配产品名称
        best_product, product_ratio = self.find_best_match(query, product_names)
        if best_product and product_ratio > result["confidence"]:
            for category in self.knowledge_base["产品信息"]:
                for product in category["products"]:
                    if product["name"] == best_product:
                        result = {
                            "response": (f"产品名称：{product['name']}\n"
                                       f"描述：{product['description']}\n"
                                       f"价格：{product['price']}\n"
                                       f"特点：\n" + "\n".join(f"- {f}" for f in product["features"])),
                            "source": "产品信息",
                            "confidence": product_ratio
                        }
        
        # 在服务指南中搜索
        guide_titles = [guide["title"] for guide in self.knowledge_base.get("服务指南", [])]
        best_guide, guide_ratio = self.find_best_match(query, guide_titles)
        
        if best_guide and guide_ratio > result["confidence"]:
            for guide in self.knowledge_base["服务指南"]:
                if guide["title"] == best_guide:
                    result = {
                        "response": f"{guide['title']}：\n{guide['content']}",
                        "source": "服务指南",
                        "confidence": guide_ratio
                    }
        
        return result["response"], result["source"] if result["confidence"] > 0 else (None, None)
    
    def append_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def send_message(self):
        user_message = self.input_box.get("1.0", tk.END).strip()
        if not user_message:
            return
            
        self.append_message(self.format_message(user_message, True))
        self.input_box.delete("1.0", tk.END)
        
        try:
            # 首先在知识库中查找
            knowledge_response, source = self.find_in_knowledge_base(user_message)
            
            if knowledge_response:
                response_prefix = {
                    "常见问题": "根据常见问题解答：\n",
                    "产品信息": "以下是相关产品信息：\n",
                    "服务指南": "以下是相关服务指南：\n"
                }.get(source, "")
                self.append_message(self.format_message(f"{response_prefix}{knowledge_response}"))
                return
            
            # 如果知识库中没有找到，使用API
            # 将知识库内容作为上下文添加到API请求中
            context = ("我是一个客服助手，我会优先使用知识库中的信息来回答问题。"
                      "如果问题与知识库内容不相关，我会根据具体情况提供合适的回答。")
            
            self.messages = []  # 清空之前的对话历史
            self.messages.append({"role": "system", "content": context})
            self.messages.append({"role": "user", "content": user_message})
            
            # 获取AI响应
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages,
                temperature=0.7
            )
            
            # 获取响应内容
            ai_message = response.choices[0].message.content
            
            # 添加AI响应到历史记录
            self.messages.append({"role": "assistant", "content": ai_message})
            
            # 显示响应
            self.append_message(self.format_message(ai_message))
            
        except Exception as e:
            self.append_message(self.format_message("抱歉，我现在无法回答您的问题。请稍后再试。"))
    
    def clear_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.messages = []
        self.append_message(
            "系统: 对话已清除。\n"
            "您好！我是您的智能客服助手。请问有什么可以帮您？\n"
            "您可以直接输入问题，或点击下方的常见问题按钮。"
        )

if __name__ == '__main__':
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop() 

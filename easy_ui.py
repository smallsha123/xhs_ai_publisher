import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
from write_xiaohongshu import XiaohongshuPoster
import json
import requests
from PIL import Image, ImageTk
import io


# 小红书发布助手ui
class XiaohongshuUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("✨ 小红书发文助手") 
        self.window.geometry("1200x650") # 缩小窗口尺寸
        self.window.configure(bg='#f8f9fa')
        
        # 设置主题样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义样式
        style.configure('TLabelframe', background='#ffffff', borderwidth=1)
        style.configure('TLabelframe.Label', font=('微软雅黑', 10, 'bold'), foreground='#2c3e50')
        style.configure('TButton', 
                       font=('微软雅黑', 9, 'bold'),
                       padding=5,
                       background='#4a90e2',
                       foreground='white',
                       borderwidth=0)
        style.configure('TLabel', font=('微软雅黑', 9), foreground='#34495e')
        style.configure('TEntry', 
                       padding=5,
                       font=('微软雅黑', 9),
                       fieldbackground='#ffffff',
                       borderwidth=1)
        
        # 初始化变量
        self.phone_var = tk.StringVar()
        self.country_code_var = tk.StringVar(value="+86") # 新增国家区号变量
        self.input_text = tk.StringVar()
        self.title_var = tk.StringVar() 
        self.subtitle_var = tk.StringVar()
        self.header_var = tk.StringVar(value="大模型技术分享")
        self.author_var = tk.StringVar(value="贝塔街的万事屋")
        
        # 国家区号字典
        self.country_codes = {
            "中国": "+86",
            "中国香港": "+852", 
            "中国台湾": "+886",
            "中国澳门": "+853",
            "新加坡": "+65",
            "马来西亚": "+60",
            "日本": "+81",
            "韩国": "+82",
            "美国": "+1",
            "加拿大": "+1",
            "英国": "+44",
            "法国": "+33",
            "德国": "+49",
            "意大利": "+39",
            "西班牙": "+34",
            "葡萄牙": "+351",
            "俄罗斯": "+7",
            "澳大利亚": "+61",
            "新西兰": "+64",
            "印度": "+91",
            "泰国": "+66",
            "越南": "+84",
            "菲律宾": "+63",
            "印度尼西亚": "+62",
            "阿联酋": "+971",
            "沙特阿拉伯": "+966",
            "巴西": "+55",
            "墨西哥": "+52",
            "南非": "+27",
            "埃及": "+20"
        }
        
        # 创建主滚动容器
        self.canvas = tk.Canvas(self.window, bg='#f8f9fa')
        self.scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 设置主容器
        self.main_container = ttk.Frame(self.scrollable_frame, padding="25 15 25 15")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # 布局滚动组件
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.create_widgets()
        
        self.images = []
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def create_widgets(self):
        # 手机号输入
        phone_frame = ttk.LabelFrame(self.main_container, text="🔐 登录信息", padding=15)
        phone_frame.pack(fill="x", pady=(0,15))
        
        # 新增国家区号下拉框
        ttk.Label(phone_frame, text="🌏 国家区号:").pack(side="left")
        country_combobox = ttk.Combobox(phone_frame, textvariable=self.country_code_var, width=15)
        country_combobox['values'] = [f"{country}({code})" for country, code in self.country_codes.items()]
        country_combobox.set("中国(+86)")  # 设置默认值
        country_combobox.pack(side="left", padx=15)
        
        # 当选择改变时更新country_code_var
        def on_country_select(event):
            selected = country_combobox.get()
            country_code = selected.split('(')[1].replace(')', '')
            self.country_code_var.set(country_code)
        country_combobox.bind('<<ComboboxSelected>>', on_country_select)
        
        ttk.Label(phone_frame, text="📱 手机号:").pack(side="left")
        phone_entry = ttk.Entry(phone_frame, textvariable=self.phone_var, width=30)
        phone_entry.pack(side="left", padx=15)
        login_btn = ttk.Button(phone_frame, text="🚀 登录", command=self.login, style='TButton')
        login_btn.pack(side="left")
        
        # 操作按钮区域
        button_frame = ttk.Frame(self.main_container)
        button_frame.pack(fill="x", pady=(0,15))
        
        generate_btn = ttk.Button(button_frame, text="✨ 生成内容", command=self.generate_content, style='TButton')
        generate_btn.pack(side="left", padx=(0,15))
        
        preview_btn = ttk.Button(button_frame, text="🎯 预览发布", command=self.preview_post, style='TButton')
        preview_btn.pack(side="left")

        # 左右布局容器
        content_container = ttk.Frame(self.main_container)
        content_container.pack(fill=tk.BOTH, expand=True)
        
        # 左侧内容区域
        left_frame = ttk.Frame(content_container)
        left_frame.pack(side="left", fill=tk.BOTH, expand=True, padx=(0,15))
         
        # 输入区域
        input_frame = ttk.LabelFrame(left_frame, text="✏️ 内容输入", padding=15)
        input_frame.pack(fill="both", expand=True, pady=(0,15))
        
        self.input_text_widget = scrolledtext.ScrolledText(
            input_frame, 
            height=8,
            font=('微软雅黑', 10),
            wrap=tk.WORD,
            bg='#ffffff',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        self.input_text_widget.pack(fill="both", expand=True)
        
        # 标题编辑区
        title_frame = ttk.LabelFrame(left_frame, text="📝 标题编辑", padding=15)
        title_frame.pack(fill="x")
        
        # 使用Grid布局管理标题区域
        for i, (label_text, var) in enumerate([
            ("📌 标题:", self.title_var),
            ("📄 内容:", self.subtitle_var),
            ("🏷️ 眉头标题:", self.header_var),
            ("👤 作者:", self.author_var)
        ]):
            ttk.Label(title_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=8)
            if label_text == "📄 内容:":
                entry = ttk.Entry(title_frame, textvariable=var, width=45)
            else:
                entry = ttk.Entry(title_frame, textvariable=var, width=35)
            entry.grid(row=i, column=1, padx=15, pady=8, sticky="ew")
        
        title_frame.grid_columnconfigure(1, weight=1)
        
        # 右侧图片预览区
        self.preview_frame = ttk.LabelFrame(content_container, text="🖼️ 图片预览", padding=15)
        self.preview_frame.pack(side="right", fill="both", expand=True)
        
        # 创建图片预览的画布和滚动条
        self.preview_canvas = tk.Canvas(self.preview_frame, bg='#ffffff')
        self.preview_scrollbar = ttk.Scrollbar(self.preview_frame, orient="vertical", command=self.preview_canvas.yview)
        self.preview_container = ttk.Frame(self.preview_canvas)
        
        self.preview_container.bind(
            "<Configure>",
            lambda e: self.preview_canvas.configure(
                scrollregion=self.preview_canvas.bbox("all")
            )
        )
        
        self.preview_canvas.create_window((0, 0), window=self.preview_container, anchor="nw")
        self.preview_canvas.configure(yscrollcommand=self.preview_scrollbar.set)
        
        self.preview_canvas.pack(side="left", fill="both", expand=True)
        self.preview_scrollbar.pack(side="right", fill="y")

    def login(self):
        try:
            phone = self.phone_var.get()
            country_code = self.country_code_var.get()
            if not phone:
                messagebox.showerror("❌ 错误", "请输入手机号")
                return
                
            self.poster = XiaohongshuPoster()
            self.poster.login(phone, country_code=country_code)
            messagebox.showinfo("✅ 成功", "登录成功")
        except Exception as e:
            messagebox.showerror("❌ 错误", f"登录失败: {str(e)}")

    def generate_content(self):
        try:
            input_text = self.input_text_widget.get("1.0", tk.END).strip()
            if not input_text:
                messagebox.showerror("❌ 错误", "请输入内容")
                return
                
            workflow_id = "7431484143153070132"
            parameters = {
                "BOT_USER_INPUT": input_text,
                "HEADER_TITLE": self.header_var.get(),
                "AUTHOR": self.author_var.get()
            }
            
            # 调用API
            response = requests.post(
                "http://8.137.103.115:8081/workflow/run",
                json={
                    "workflow_id": workflow_id,
                    "parameters": parameters
                }
            )
            print(response.content)
            
            if response.status_code != 200:
                raise Exception("API调用失败")
                
            res = response.json()
            
            # 解析返回结果
            print(res)
            output_data = json.loads(res['data'])
            title = json.loads(output_data['output'])['title']
            self.title_var.set(title)
            
            # 获取生成的内容作为副标题
            content = output_data['content']
            self.subtitle_var.set(content)
            
            # 获取图片
            cover_image_url = json.loads(res['data'])['image']
            content_image_urls = json.loads(res['data'])['image_content']
            
            # 清空之前的图片
            for widget in self.preview_container.winfo_children():
                widget.destroy()
            
            # 下载并显示图片
            self.images = []
            self.download_and_show_image(cover_image_url, "封面图")
            for i, url in enumerate(content_image_urls):
                self.download_and_show_image(url, f"内容图{i+1}")
                
            # 显示生成的内容
            self.input_text_widget.delete("1.0", tk.END)
            self.input_text_widget.insert("1.0", input_text)
            
            messagebox.showinfo("✅ 成功", "✨ 内容生成完成")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("❌ 错误", f"生成内容失败: {str(e)}\n{error_details}")

    def download_and_show_image(self, url, title):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # 保存图片
                img_path = os.path.join(os.path.dirname(__file__), f'{title}.jpg')
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                self.images.append(img_path)
                
                # 显示图片预览
                image = Image.open(io.BytesIO(response.content))
                image = image.resize((125, 125), Image.LANCZOS)  # 缩小预览图尺寸
                photo = ImageTk.PhotoImage(image)
                
                frame = ttk.Frame(self.preview_container)
                frame.pack(side="top", pady=10)
                
                label = ttk.Label(frame, image=photo)
                label.image = photo
                label.pack()
                ttk.Label(frame, text=title, font=('微软雅黑', 9, 'bold')).pack(pady=(8,0))
                
        except Exception as e:
            print(f"下载图片失败: {str(e)}")

    def preview_post(self):
        try:
            if not hasattr(self, 'poster'):
                messagebox.showerror("❌ 错误", "请先登录")
                return
                
            title = self.title_var.get()
            content = self.subtitle_var.get()
                
            self.poster.post_article(title, content, self.images)
            messagebox.showinfo("✅ 成功", "🎉 文章已准备好,请在浏览器中检查并发布")
            
        except Exception as e:
            messagebox.showerror("❌ 错误", f"预览发布失败: {str(e)}")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = XiaohongshuUI()
    app.run()
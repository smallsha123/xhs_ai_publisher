import sys
import signal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QFrame,
                           QProgressBar, QScrollArea, QGraphicsView, QGraphicsScene, QGraphicsOpacityEffect,
                           QStackedWidget)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPalette, QColor, QPainter, QPen, QBrush
import os
from src.core.write_xiaohongshu import XiaohongshuPoster
import json
import requests
from PIL import Image
import io
import threading
from PyQt6.QtCore import QEvent

class LoadingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 创建遮罩层
        self.mask = QGraphicsView(parent)
        self.mask.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.mask.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.mask.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mask.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mask.setStyleSheet("background: transparent;")
        self.mask.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.mask.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 创建场景
        self.scene = QGraphicsScene()
        self.mask.setScene(self.scene)
        # 创建半透明遮罩矩形
        self.rect_item = self.scene.addRect(0, 0, parent.width(), parent.height(), 
                                          QPen(Qt.PenStyle.NoPen),
                                          QBrush(QColor(0, 0, 0, 128)))  # 128 = 0.5 * 255
        self.mask.setGeometry(parent.geometry())
        self.mask.show()
        self.mask.raise_()
        
        # 设置遮罩层事件过滤器，阻止所有鼠标事件
        self.mask.installEventFilter(self)
        
        # 连接主窗口的 resize 事件
        if parent:
            parent.resizeEvent = lambda e: self.update_mask_geometry()
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(248, 249, 250, 0.95);
                border-radius: 10px;
                border: 1px solid #ddd;
            }
            QLabel {
                border: none;
                background: transparent;
                color: #2c3e50;
            }
            QProgressBar {
                border: none;
                background-color: #e9ecef;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 5px;
            }
        """)
        
        # 设置固定大小
        self.setFixedSize(300, 150)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 加载提示文字
        loading_label = QLabel("✨ 正在生成内容...", self)
        loading_label.setStyleSheet(f"""
            font-family: {("Menlo" if sys.platform == "darwin" else "Consolas")};
            font-size: 14pt;
            font-weight: bold;
            color: #2c3e50;
        """)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(loading_label)
        
        # 进度条
        self.progress = QProgressBar(self)
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                min-height: 8px;
                max-height: 8px;
            }
        """)
        layout.addWidget(self.progress)
        
        # 提示文字
        tip_label = QLabel("请稍候，正在为您生成精美内容", self)
        tip_label.setStyleSheet(f"""
            font-family: {("Menlo" if sys.platform == "darwin" else "Consolas")};
            font-size: 12pt;
            color: #666;
        """)
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tip_label)
        
        # 设置初始透明度
        self.setWindowOpacity(0)
        
        # 淡入动画
        self.animation = QTimer()
        self.animation.timeout.connect(self._fade_step)
        self.opacity = 0.0
    
    def eventFilter(self, obj, event):
        # 阻止遮罩层的所有鼠标事件
        if obj == self.mask and event.type() in [
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseButtonDblClick,
            QEvent.Type.MouseMove
        ]:
            return True
        return super().eventFilter(obj, event)
    
    def update_mask_geometry(self):
        if self.parent():
            # 获取主窗口的几何信息
            parent_rect = self.parent().geometry()
            # 更新遮罩层大小和位置
            self.mask.setGeometry(0, 0, parent_rect.width(), parent_rect.height())
            # 更新场景大小
            self.scene.setSceneRect(0, 0, parent_rect.width(), parent_rect.height())
            # 更新矩形大小
            self.rect_item.setRect(0, 0, parent_rect.width(), parent_rect.height())
            self.mask.raise_()
            self.mask.show()
            
            # 更新加载窗口位置
            x = (parent_rect.width() - self.width()) // 2
            y = (parent_rect.height() - self.height()) // 2
            self.move(x, y)
    
    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            # 更新遮罩层大小和位置
            self.update_mask_geometry()
            # 确保遮罩层和加载窗口在最上层
            self.mask.raise_()
            self.raise_()
            # 开始淡入动画
            self.animation.start(30)
    
    def closeEvent(self, event):
        # 关闭遮罩层
        if hasattr(self, 'mask'):
            self.mask.close()
        super().closeEvent(event)
    
    def _fade_step(self):
        if self.opacity >= 1.0:
            self.animation.stop()
            return
        self.opacity += 0.1
        self.setWindowOpacity(self.opacity)

class TipWindow(QWidget):
    def __init__(self, parent=None, message="", duration=2000):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建消息框
        self.msg_frame = QFrame()
        self.msg_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 10px;
            }
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        
        # 消息框布局
        msg_layout = QHBoxLayout(self.msg_frame)
        msg_layout.setContentsMargins(20, 15, 20, 15)
        msg_layout.setSpacing(15)
        
        # 设置图标和颜色
        if "❌" in message:
            icon = "❌"
            color = "#e74c3c"
        elif "✅" in message:
            icon = "✅"
            color = "#2ecc71"
        else:
            icon = "ℹ️"
            color = "#3498db"
        
        # 清理消息文本
        message = message.replace("❌", "").replace("✅", "").strip()
        
        # 创建图标标签
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 24px;
            color: {color};
            padding: 0;
            margin: 0;
        """)
        msg_layout.addWidget(icon_label)
        
        # 创建消息标签
        msg_label = QLabel(message)
        msg_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            padding: 0;
            margin: 0;
        """)
        msg_label.setWordWrap(True)
        msg_layout.addWidget(msg_label, 1)
        
        # 将消息框添加到主布局
        layout.addWidget(self.msg_frame)
        
        # 设置固定宽度和调整大小
        self.setFixedWidth(400)
        self.adjustSize()
        
        # 设置动画效果
        self.setWindowOpacity(0)
        
        # 设置定时器
        self.fade_in_timer = QTimer(self)
        self.fade_in_timer.timeout.connect(self.fade_in_step)
        self.fade_in_timer.start(20)
        
        self.fade_out_timer = QTimer(self)
        self.fade_out_timer.timeout.connect(self.fade_out_step)
        QTimer.singleShot(duration, self.fade_out_timer.start)
        
        self.opacity = 0.0
        
    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            # 获取主窗口的实际位置和大小
            parent_size = self.parent().size()
            
            # 计算弹窗位置，使其在主窗口中心
            x = (parent_size.width() - self.width()) // 2
            y = 30
            # 移动到计算出的位置
            self.move(x, y)
    
    def fade_in_step(self):
        if self.opacity >= 1.0:
            self.fade_in_timer.stop()
            return
        self.opacity += 0.1
        self.setWindowOpacity(self.opacity)
    
    def fade_out_step(self):
        if self.opacity <= 0.0:
            self.fade_out_timer.stop()
            self.close()
            return
        self.opacity -= 0.1
        self.setWindowOpacity(self.opacity)

class ContentGeneratorThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, input_text, header_title, author):
        super().__init__()
        self.input_text = input_text
        self.header_title = header_title
        self.author = author
    
    def run(self):
        try:
            workflow_id = "7431484143153070132"
            parameters = {
                "BOT_USER_INPUT": self.input_text,
                "HEADER_TITLE": self.header_title,
                "AUTHOR": self.author
            }
            
            response = requests.post(
                "http://8.137.103.115:8081/workflow/run",
                json={
                    "workflow_id": workflow_id,
                    "parameters": parameters
                }
            )
            
            if response.status_code != 200:
                raise Exception("API调用失败")
            
            res = response.json()
            output_data = json.loads(res['data'])
            title = json.loads(output_data['output'])['title']
            
            result = {
                'title': title,
                'content': output_data['content'],
                'cover_image': json.loads(res['data'])['image'],
                'content_images': json.loads(res['data'])['image_content'],
                'input_text': self.input_text
            }
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ImageProcessorThread(QThread):
    finished = pyqtSignal(list, list)  # 发送图片路径列表和图片信息列表
    error = pyqtSignal(str)
    
    def __init__(self, cover_image_url, content_image_urls):
        super().__init__()
        self.cover_image_url = cover_image_url
        self.content_image_urls = content_image_urls
    
    def run(self):
        try:
            images = []
            image_list = []
            
            # 处理封面图
            if self.cover_image_url:
                img_path, pixmap_info = self.process_image(self.cover_image_url, "封面图")
                if img_path and pixmap_info:
                    images.append(img_path)
                    image_list.append(pixmap_info)
            
            # 处理内容图
            for i, url in enumerate(self.content_image_urls):
                img_path, pixmap_info = self.process_image(url, f"内容图{i+1}")
                if img_path and pixmap_info:
                    images.append(img_path)
                    image_list.append(pixmap_info)
            
            self.finished.emit(images, image_list)
        except Exception as e:
            self.error.emit(str(e))
    
    def process_image(self, url, title):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # 保存图片
                img_path = os.path.join(os.path.dirname(__file__), f'static/images/{title}.jpg')
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                
                # 保存原始图片
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                # 处理图片预览
                image = Image.open(io.BytesIO(response.content))
                
                # 计算缩放比例，保持宽高比
                width, height = image.size
                max_size = 360  # 调整预览图片的最大尺寸
                scale = min(max_size/width, max_size/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                # 缩放图片
                image = image.resize((new_width, new_height), Image.LANCZOS)
                
                # 创建白色背景
                background = Image.new('RGB', (max_size, max_size), 'white')
                # 将图片粘贴到中心位置
                offset = ((max_size - new_width) // 2, (max_size - new_height) // 2)
                background.paste(image, offset)
                
                # 转换为QPixmap
                img_bytes = io.BytesIO()
                background.save(img_bytes, format='PNG')
                img_data = img_bytes.getvalue()
                
                qimage = QImage.fromData(img_data)
                pixmap = QPixmap.fromImage(qimage)
                
                if pixmap.isNull():
                    raise Exception("无法创建有效的图片预览")
                
                return img_path, {'pixmap': pixmap, 'title': title}
            else:
                raise Exception(f"下载图片失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"处理图片失败: {str(e)}")
            return None, None

class XiaohongshuUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化国家区号
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
        
        self.setWindowTitle("✨ 小红书发文助手")
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #f8f9fa;
            }}
            QLabel {{
                font-family: {("Menlo" if sys.platform == "darwin" else "Consolas")};
                color: #34495e;
                font-size: 11pt;
                border: none;
                background: transparent;
            }}
            QPushButton {{
                font-family: {("Menlo" if sys.platform == "darwin" else "Consolas")};
                font-size: 11pt;
                font-weight: bold;
                padding: 6px;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #357abd;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
            }}
            QLineEdit, QTextEdit, QComboBox {{
                font-family: {("Menlo" if sys.platform == "darwin" else "Consolas")};
                font-size: 11pt;
                padding: 4px;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            QFrame {{
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 6px;
            }}
            QScrollArea {{
                border: none;
            }}
            #sidebar {{
                background-color: #2c3e50;
                min-width: 60px;
                max-width: 60px;
                padding: 20px 0;
            }}
            #sidebar QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 0;
                color: #ecf0f1;
                padding: 15px 0;
                margin: 5px 0;
                font-size: 20px;
            }}
            #sidebar QPushButton:hover {{
                background-color: #34495e;
            }}
            #sidebar QPushButton:checked {{
                background-color: #34495e;
            }}
            #settingsPage {{
                background-color: white;
                padding: 20px;
            }}
        """)
        
        self.setMinimumSize(1000, 600)
        self.center()
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建水平布局
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建侧边栏
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # 创建侧边栏按钮
        home_btn = QPushButton("🏠")
        home_btn.setCheckable(True)
        home_btn.setChecked(True)
        home_btn.clicked.connect(lambda: self.switch_page(0))
        
        settings_btn = QPushButton("⚙️")
        settings_btn.setCheckable(True)
        settings_btn.clicked.connect(lambda: self.switch_page(1))
        
        sidebar_layout.addWidget(home_btn)
        sidebar_layout.addWidget(settings_btn)
        sidebar_layout.addStretch()
        
        # 添加侧边栏到主布局
        main_layout.addWidget(sidebar)
        
        # 创建堆叠窗口部件
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # 创建主页面
        home_page = QWidget()
        home_layout = QVBoxLayout(home_page)
        home_layout.setContentsMargins(15, 10, 15, 10)
        home_layout.setSpacing(8)
        
        # 创建设置页面
        settings_page = QWidget()
        settings_page.setObjectName("settingsPage")
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(10)
        
        # 添加版本信息
        version_label = QLabel("版本号: v1.0.0")
        version_label.setStyleSheet("""
            font-size: 14pt;
            color: #2c3e50;
            font-weight: bold;
        """)
        settings_layout.addWidget(version_label)
        settings_layout.addStretch()
        
        # 将页面添加到堆叠窗口
        self.stack.addWidget(home_page)
        self.stack.addWidget(settings_page)
        
        # 初始化变量
        self.images = []
        self.image_list = []
        self.current_image_index = 0
        
        # 创建占位图
        self.placeholder_photo = QPixmap(200, 200)
        self.placeholder_photo.fill(QColor('#f8f9fa'))
        
        # 创建登录区域
        self.create_login_section(home_layout)
        
        # 创建内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        home_layout.addLayout(content_layout)
        
        # 创建左侧区域
        self.create_left_section(content_layout)
        
        # 创建右侧预览区域
        self.create_preview_section(content_layout)
    
    def center(self):
        """将窗口移动到屏幕中央"""
        # 获取屏幕几何信息
        screen = QApplication.primaryScreen().geometry()
        # 获取窗口几何信息
        size = self.geometry()
        # 计算居中位置
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        # 移动窗口
        self.move(x, y)
    
    def create_login_section(self, parent_layout):
        login_frame = QFrame()
        login_frame.setStyleSheet("""
            QFrame {
                padding: 8px;
                background-color: white;
            }
            QLabel {
                font-size: 11pt;
                border: none;
                background: transparent;
            }
        """)
        login_layout = QHBoxLayout(login_frame)
        login_layout.setContentsMargins(8, 8, 8, 8)
        login_layout.setSpacing(8)
        
        # 添加标题标签
        title_label = QLabel("🔐 登录信息")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #2c3e50;")
        login_layout.addWidget(title_label)
        
        # 国家区号选择
        login_layout.addWidget(QLabel("🌏 国家区号:"))
        self.country_combo = QComboBox()
        self.country_combo.addItems([f"{country}({code})" for country, code in self.country_codes.items()])
        self.country_combo.setCurrentText("中国(+86)")
        self.country_combo.setFixedWidth(160)  # 减小宽度
        login_layout.addWidget(self.country_combo)
        
        # 手机号输入
        login_layout.addWidget(QLabel("📱 手机号:"))
        self.phone_input = QLineEdit()
        self.phone_input.setFixedWidth(160)  # 减小宽度
        login_layout.addWidget(self.phone_input)
        
        # 登录按钮
        login_btn = QPushButton("🚀 登录")
        login_btn.setFixedWidth(80)  # 减小宽度
        login_btn.clicked.connect(self.login)
        login_layout.addWidget(login_btn)
        
        login_layout.addStretch()
        parent_layout.addWidget(login_frame)
    
    def create_left_section(self, parent_layout):
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(8)  # 减小间距
        
        # 标题编辑区域
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                padding: 12px;
                background-color: white;
            }
            QLabel {
                font-size: 11pt;
                color: #2c3e50;
                border: none;
                background: transparent;
            }
            QLineEdit {
                padding: 4px;
                margin-bottom: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                max-height: 24px;
                min-width: 200px;
            }
            QLabel#section_title {
                font-size: 12pt;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setSpacing(0)
        title_layout.setContentsMargins(12, 12, 12, 12)
        
        # 添加标题标签
        header_label = QLabel("✏️ 标题编辑")
        header_label.setObjectName("section_title")
        title_layout.addWidget(header_label)
        
        # 标题输入框
        title_input_layout = QHBoxLayout()
        title_input_layout.setSpacing(8)
        title_label = QLabel("📌 标题")
        title_label.setFixedWidth(100)  # 增加标签宽度
        title_input_layout.addWidget(title_label)
        self.title_input = QLineEdit()
        title_input_layout.addWidget(self.title_input)
        title_layout.addLayout(title_input_layout)
        
        # 内容输入框
        content_input_layout = QHBoxLayout()
        content_input_layout.setSpacing(8)
        content_label = QLabel("📄 内容")
        content_label.setFixedWidth(100)  # 增加标签宽度
        content_input_layout.addWidget(content_label)
        self.subtitle_input = QLineEdit()
        content_input_layout.addWidget(self.subtitle_input)
        title_layout.addLayout(content_input_layout)
        
        # 眉头标题输入框
        header_input_layout = QHBoxLayout()
        header_input_layout.setSpacing(8)
        header_label = QLabel("🏷️ 眉头标题")
        header_label.setFixedWidth(100)  # 增加标签宽度
        header_input_layout.addWidget(header_label)
        self.header_input = QLineEdit("大模型技术分享")
        self.header_input.setMinimumWidth(250)  # 增加输入框最小宽度
        header_input_layout.addWidget(self.header_input)
        title_layout.addLayout(header_input_layout)
        
        # 作者输入框
        author_input_layout = QHBoxLayout()
        author_input_layout.setSpacing(8)
        author_label = QLabel("👤 作者")
        author_label.setFixedWidth(100)  # 增加标签宽度
        author_input_layout.addWidget(author_label)
        self.author_input = QLineEdit("贝塔街的万事屋")
        self.author_input.setMinimumWidth(250)  # 增加输入框最小宽度
        author_input_layout.addWidget(self.author_input)
        title_layout.addLayout(author_input_layout)
        
        # 内容输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                padding: 12px;
                background-color: white;
                margin-top: 8px;
            }
            QLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 8px;
                border: none;
                background: transparent;
            }
            QTextEdit {
                font-size: 11pt;
                line-height: 1.5;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                min-width: 100px;
                padding: 8px 15px;
                font-weight: bold;
                margin-top: 10px;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(0)
        input_layout.setContentsMargins(12, 12, 12, 12)
        
        input_label = QLabel("✏️ 内容输入")
        input_layout.addWidget(input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setMinimumHeight(120)  # 减小高度
        input_layout.addWidget(self.input_text)
        
        # 添加按钮区域到内容输入框下面
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        generate_btn = QPushButton("✨ 生成内容")
        generate_btn.clicked.connect(self.generate_content)
        button_layout.addWidget(generate_btn)
        
        preview_btn = QPushButton("🎯 预览发布")
        preview_btn.clicked.connect(self.preview_post)
        button_layout.addWidget(preview_btn)
        
        button_layout.addStretch()
        input_layout.addLayout(button_layout)
        
        # 添加到主布局
        left_layout.addWidget(title_frame)
        left_layout.addWidget(input_frame)
        parent_layout.addWidget(left_widget)
    
    def create_preview_section(self, parent_layout):
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                padding: 15px;
                background-color: white;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
            }
            QLabel {
                font-size: 11pt;
                color: #2c3e50;
                border: none;
                background: transparent;
            }
            QWidget#image_container {
                background-color: white;
            }
            QPushButton {
                padding: 15px;
                font-weight: bold;
                border-radius: 20px;
                background-color: rgba(74, 144, 226, 0.1);
                color: #4a90e2;
            }
            QPushButton:hover {
                background-color: rgba(74, 144, 226, 0.2);
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #aaa;
            }
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setSpacing(15)
        preview_layout.setContentsMargins(15, 15, 15, 15)
        
        # 添加标题标签
        header_layout = QHBoxLayout()
        title_label = QLabel("🖼️ 图片预览")
        title_label.setStyleSheet("font-size: 13pt; font-weight: bold; color: #2c3e50; padding-bottom: 5px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        preview_layout.addLayout(header_layout)
        
        # 图片预览区域（包含左右按钮）
        image_preview_layout = QHBoxLayout()
        image_preview_layout.setSpacing(10)
        image_preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 左侧按钮
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.clicked.connect(self.prev_image)
        image_preview_layout.addWidget(self.prev_btn)
        
        # 图片容器
        image_container = QWidget()
        image_container.setFixedSize(380, 380)
        image_container.setStyleSheet("""
            background-color: white;
            border: 2px solid #e1e4e8;
            border-radius: 8px;
        """)
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setContentsMargins(5, 5, 5, 5)
        image_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(360, 360)
        self.image_label.setStyleSheet("border: none;")
        image_container_layout.addWidget(self.image_label)
        
        image_preview_layout.addWidget(image_container)
        
        # 右侧按钮
        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.clicked.connect(self.next_image)
        image_preview_layout.addWidget(self.next_btn)
        
        preview_layout.addLayout(image_preview_layout)
        
        # 图片标题
        self.image_title = QLabel("暂无图片")
        self.image_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_title.setStyleSheet("""
            font-weight: bold;
            color: #2c3e50;
            font-size: 12pt;
            padding: 10px 0;
        """)
        preview_layout.addWidget(self.image_title)
        
        # 初始化时禁用按钮
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        
        parent_layout.addWidget(preview_frame)
    
    def login(self):
        try:
            phone = self.phone_input.text()
            country_code = self.country_combo.currentText().split('(')[1].replace(')', '')
            
            if not phone:
                TipWindow(self, "❌ 请输入手机号").show()
                return
            
            self.poster = XiaohongshuPoster()
            self.poster.login(phone, country_code=country_code)
            TipWindow(self, "✅ 登录成功").show()
        except Exception as e:
            TipWindow(self, f"❌ 登录失败: {str(e)}").show()
    
    def generate_content(self):
        try:
            input_text = self.input_text.toPlainText().strip()
            if not input_text:
                TipWindow(self, "❌ 请输入内容").show()
                return
            
            # 显示加载窗口
            self.loading_window = LoadingWindow(self)
            self.loading_window.show()
            
            # 创建并启动生成线程
            self.generator_thread = ContentGeneratorThread(
                input_text,
                self.header_input.text(),
                self.author_input.text()
            )
            self.generator_thread.finished.connect(self.handle_generation_result)
            self.generator_thread.error.connect(self.handle_generation_error)
            self.generator_thread.start()
            
        except Exception as e:
            TipWindow(self, f"❌ 生成内容失败: {str(e)}").show()
    
    def handle_generation_result(self, result):
        self.loading_window.close()
        self.update_ui_after_generate(
            result['title'],
            result['content'],
            result['cover_image'],
            result['content_images'],
            result['input_text']
        )
    
    def handle_generation_error(self, error_msg):
        self.loading_window.close()
        TipWindow(self, f"❌ 生成内容失败: {error_msg}").show()
    
    def update_ui_after_generate(self, title, content, cover_image_url, content_image_urls, input_text):
        try:
            # 更新标题和内容
            self.title_input.setText(title if title else "")
            self.subtitle_input.setText(content if content else "")
            
            # 安全地更新文本编辑器内容
            if input_text:
                self.input_text.clear()  # 先清空内容
                self.input_text.setPlainText(input_text)  # 使用setPlainText而不是setText
            else:
                self.input_text.clear()
            
            # 清空之前的图片列表
            self.images = []
            self.image_list = []
            self.current_image_index = 0
            
            # 显示占位图
            self.image_label.setPixmap(self.placeholder_photo)
            self.image_title.setText("正在加载图片...")
            
            # 创建并启动图片处理线程
            self.image_processor = ImageProcessorThread(cover_image_url, content_image_urls)
            self.image_processor.finished.connect(self.handle_image_processing_result)
            self.image_processor.error.connect(self.handle_image_processing_error)
            self.image_processor.start()
            
        except Exception as e:
            print(f"更新UI时出错: {str(e)}")
            TipWindow(self, f"❌ 更新内容失败: {str(e)}").show()
    
    def handle_image_processing_result(self, images, image_list):
        try:
            self.images = images
            self.image_list = image_list
            
            # 打印调试信息
            print(f"收到图片处理结果: {len(images)} 张图片")
            
            if self.image_list:
                # 确保当前索引有效
                self.current_image_index = 0
                # 显示第一张图片
                current_image = self.image_list[self.current_image_index]
                if current_image and 'pixmap' in current_image:
                    self.image_label.setPixmap(current_image['pixmap'])
                    self.image_title.setText(current_image['title'])
                    # 更新按钮状态
                    self.prev_btn.setEnabled(len(self.image_list) > 1)
                    self.next_btn.setEnabled(len(self.image_list) > 1)
                else:
                    raise Exception("图片数据无效")
            else:
                raise Exception("没有可显示的图片")
                
        except Exception as e:
            print(f"处理图片结果时出错: {str(e)}")
            self.image_label.setPixmap(self.placeholder_photo)
            self.image_title.setText("图片加载失败")
            TipWindow(self, f"❌ 图片加载失败: {str(e)}").show()
    
    def handle_image_processing_error(self, error_msg):
        self.image_label.setPixmap(self.placeholder_photo)
        self.image_title.setText("图片加载失败")
        TipWindow(self, f"❌ 图片处理失败: {error_msg}").show()
    
    def show_current_image(self):
        if not self.image_list:
            self.image_label.setPixmap(self.placeholder_photo)
            self.image_title.setText("暂无图片")
            self.update_button_states()
            return
        
        current_image = self.image_list[self.current_image_index]
        self.image_label.setPixmap(current_image['pixmap'])
        self.image_title.setText(current_image['title'])
        self.update_button_states()
    
    def update_button_states(self):
        has_images = bool(self.image_list)
        self.prev_btn.setEnabled(has_images)
        self.next_btn.setEnabled(has_images)
    
    def prev_image(self):
        if self.image_list:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_list)
            self.show_current_image()
    
    def next_image(self):
        if self.image_list:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_list)
            self.show_current_image()
    
    def preview_post(self):
        try:
            if not hasattr(self, 'poster'):
                TipWindow(self, "❌ 请先登录").show()
                return
            
            title = self.title_input.text()
            content = self.subtitle_input.text()
            
            self.poster.post_article(title, content, self.images)
            TipWindow(self, "🎉 文章已准备好，请在浏览器中检查并发布").show()
            
        except Exception as e:
            TipWindow(self, f"❌ 预览发布失败: {str(e)}").show()
    
    def switch_page(self, index):
        # 切换页面
        self.stack.setCurrentIndex(index)
        
        # 更新按钮状态
        sidebar = self.findChild(QWidget, "sidebar")
        if sidebar:
            buttons = [btn for btn in sidebar.findChildren(QPushButton)]
            for i, btn in enumerate(buttons):
                btn.setChecked(i == index)

if __name__ == "__main__":
    # 设置信号处理
    def signal_handler(signum, frame):
        print("\n正在退出程序...")
        QApplication.quit()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    app = QApplication(sys.argv)
    
    # 允许 CTRL+C 中断
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)
    
    window = XiaohongshuUI()
    window.show()
    sys.exit(app.exec())
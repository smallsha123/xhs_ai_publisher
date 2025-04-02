import logging
import sys
import signal
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QFrame,
                             QStackedWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QColor, QIcon
import os
from src.core.content_processor import ContentGeneratorThread
from src.core.img_processor import ImageProcessorThread
from src.core.browser import BrowserThread
from src.config.config import Config
from src.logger.logger import Logger

from src.core.alert import TipWindow

from src.config.constants import VERSION


# 设置日志文件路径
log_path = os.path.expanduser('~/Desktop/xhsai_error.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG)


class XiaohongshuUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = Config()

        # 设置应用图标 - 需要在应用级别设置
        icon_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'build/icon.png')
        self.app_icon = QIcon(icon_path)
        QApplication.setWindowIcon(self.app_icon)  # 设置应用级别的图标
        self.setWindowIcon(self.app_icon)  # 设置窗口图标

        # 加载logger
        app_config = self.config.get_app_config()
        self.logger = Logger(is_console=app_config)

        self.logger.success("小红书发文助手启动")

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
        version_label = QLabel(f"版本号: v{VERSION}")
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

        # 创建浏览器线程
        self.browser_thread = BrowserThread()
        # 连接信号
        self.browser_thread.login_status_changed.connect(
            self.update_login_button)
        self.browser_thread.preview_status_changed.connect(
            self.update_preview_button)
        self.browser_thread.login_success.connect(self.handle_poster_ready)
        self.browser_thread.login_error.connect(self.handle_login_error)
        self.browser_thread.preview_success.connect(self.handle_preview_result)
        self.browser_thread.preview_error.connect(self.handle_preview_error)
        self.browser_thread.start()

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
        login_layout = QVBoxLayout(login_frame)  # 改为垂直布局
        login_layout.setContentsMargins(8, 8, 8, 8)
        login_layout.setSpacing(8)

        # 创建水平布局用于登录控件
        login_controls = QHBoxLayout()
        login_controls.setSpacing(8)

        # 手机号输入
        login_controls.addWidget(QLabel("📱 手机号:"))
        self.phone_input = QLineEdit()
        self.phone_input.setFixedWidth(160)  # 减小宽度
        self.phone_input.setText("15239851762")  # 设置默认值
        login_controls.addWidget(self.phone_input)

        # 登录按钮
        login_btn = QPushButton("🚀 登录")
        login_btn.setObjectName("login_btn")  # 添加对象名称
        login_btn.setFixedWidth(80)  # 减小宽度
        login_btn.clicked.connect(self.login)
        login_controls.addWidget(login_btn)

        # 添加免责声明
        disclaimer_label = QLabel("⚠️ 仅限于学习,请勿用于其他用途,否则后果自负")
        disclaimer_label.setStyleSheet("""
            color: #e74c3c;
            font-size: 10pt;
            font-weight: bold;
        """)
        login_controls.addWidget(disclaimer_label)

        login_controls.addStretch()
        login_layout.addLayout(login_controls)
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

        # 眉头标题输入框
        header_input_layout = QHBoxLayout()
        header_input_layout.setSpacing(8)
        header_label = QLabel("🏷️ 眉头标题")
        header_label.setFixedWidth(100)  # 增加标签宽度
        header_input_layout.addWidget(header_label)
        self.header_input = QLineEdit(self.config.get_title_config()['title'])
        self.header_input.setMinimumWidth(250)  # 增加输入框最小宽度
        self.header_input.textChanged.connect(self.update_title_config)
        header_input_layout.addWidget(self.header_input)
        title_layout.addLayout(header_input_layout)

        # 作者输入框
        author_input_layout = QHBoxLayout()
        author_input_layout.setSpacing(8)
        author_label = QLabel("👤 作者")
        author_label.setFixedWidth(100)  # 增加标签宽度
        author_input_layout.addWidget(author_label)
        self.author_input = QLineEdit(self.config.get_title_config()['author'])
        self.author_input.setMinimumWidth(250)  # 增加输入框最小宽度
        self.author_input.textChanged.connect(self.update_author_config)
        author_input_layout.addWidget(self.author_input)
        title_layout.addLayout(author_input_layout)

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
        self.subtitle_input = QTextEdit()  # 改为QTextEdit
        self.subtitle_input.setMinimumHeight(120)  # 设置最小高度
        self.subtitle_input.setStyleSheet("""
            QTextEdit {
                font-size: 11pt;
                line-height: 1.5;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        content_input_layout.addWidget(self.subtitle_input)
        title_layout.addLayout(content_input_layout)

        # 添加垂直间距
        title_layout.addSpacing(25)  # 添加间距

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

        # 创建一个水平布局来包含输入框和按钮
        input_container = QWidget()
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(0)

        # 添加输入框
        self.input_text = QTextEdit()
        self.input_text.setMinimumHeight(120)  # 减小高度
        self.input_text.setPlainText("中医的好处")  # 设置默认值
        input_container_layout.addWidget(self.input_text)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.addStretch()  # 添加弹性空间，使按钮靠右

        # 将生成按钮保存为类属性
        self.generate_btn = QPushButton("✨ 生成内容")
        self.generate_btn.clicked.connect(self.generate_content)
        button_layout.addWidget(self.generate_btn)

        input_container_layout.addLayout(button_layout)
        input_layout.addWidget(input_container)

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
        title_label.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #2c3e50; padding-bottom: 5px;")
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

        # 添加预览发布按钮
        preview_btn = QPushButton("🎯 预览发布")
        preview_btn.setObjectName("preview_btn")
        preview_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                font-size: 12pt;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 15px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        preview_btn.clicked.connect(self.preview_post)
        preview_btn.setEnabled(False)  # 初始状态设置为禁用
        preview_layout.addWidget(
            preview_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 初始化时禁用按钮
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)

        parent_layout.addWidget(preview_frame)

    def update_login_button(self, text, enabled):
        """更新登录按钮状态"""
        login_btn = self.findChild(QPushButton, "login_btn")
        if login_btn:
            login_btn.setText(text)
            login_btn.setEnabled(enabled)

    def update_preview_button(self, text, enabled):
        """更新预览按钮状态"""
        preview_btn = self.findChild(QPushButton, "preview_btn")
        if preview_btn:
            preview_btn.setText(text)
            preview_btn.setEnabled(enabled)

    def login(self):
        try:
            phone = self.phone_input.text()

            if not phone:
                TipWindow(self, "❌ 请输入手机号").show()
                return

            # 更新登录按钮状态
            self.update_login_button("⏳ 登录中...", False)

            # 添加登录任务到浏览器线程
            self.browser_thread.action_queue.append({
                'type': 'login',
                'phone': phone
            })

        except Exception as e:
            TipWindow(self, f"❌ 登录失败: {str(e)}").show()

    def handle_login_error(self, error_msg):
        # 恢复登录按钮状态
        self.update_login_button("🚀 登录", True)
        TipWindow(self, f"❌ 登录失败: {error_msg}").show()

    def handle_poster_ready(self, poster):
        """处理登录成功后的poster对象"""
        self.poster = poster
        # 更新登录按钮状态
        self.update_login_button("✅ 已登录", False)
        TipWindow(self, "✅ 登录成功").show()

    def generate_content(self):
        try:
            input_text = self.input_text.toPlainText().strip()
            if not input_text:
                TipWindow(self, "❌ 请输入内容").show()
                return

            # 创建并启动生成线程
            self.generator_thread = ContentGeneratorThread(
                input_text,
                self.header_input.text(),
                self.author_input.text(),
                self.generate_btn  # 传递按钮引用
            )
            self.generator_thread.finished.connect(
                self.handle_generation_result)
            self.generator_thread.error.connect(self.handle_generation_error)
            self.generator_thread.start()

        except Exception as e:
            self.generate_btn.setText("✨ 生成内容")  # 恢复按钮文字
            self.generate_btn.setEnabled(True)  # 恢复按钮可点击状态
            TipWindow(self, f"❌ 生成内容失败: {str(e)}").show()

    def handle_generation_result(self, result):
        self.update_ui_after_generate(
            result['title'],
            result['content'],
            result['cover_image'],
            result['content_images'],
            result['input_text']
        )

    def handle_generation_error(self, error_msg):
        TipWindow(self, f"❌ 生成内容失败: {error_msg}").show()

    def update_ui_after_generate(self, title, content, cover_image_url, content_image_urls, input_text):
        try:
            # 创建并启动图片处理线程
            self.image_processor = ImageProcessorThread(
                cover_image_url, content_image_urls)
            self.image_processor.finished.connect(
                self.handle_image_processing_result)
            self.image_processor.error.connect(
                self.handle_image_processing_error)
            self.image_processor.start()

            # 更新标题和内容
            self.title_input.setText(title if title else "")
            self.subtitle_input.setText(content if content else "")

            # 安全地更新文本编辑器内容
            if input_text:
                self.input_text.clear()  # 先清空内容
                # 使用setPlainText而不是setText
                self.input_text.setPlainText(input_text)
            else:
                self.input_text.clear()

            # 清空之前的图片列表
            self.images = []
            self.image_list = []
            self.current_image_index = 0

            # 显示占位图
            self.image_label.setPixmap(self.placeholder_photo)
            self.image_title.setText("正在加载图片...")

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
                    # 启用预览发布按钮
                    self.update_preview_button("🎯 预览发布", True)
                else:
                    raise Exception("图片数据无效")
            else:
                raise Exception("没有可显示的图片")

        except Exception as e:
            print(f"处理图片结果时出错: {str(e)}")
            self.image_label.setPixmap(self.placeholder_photo)
            self.image_title.setText("图片加载失败")
            # 禁用预览发布按钮
            self.update_preview_button("🎯 预览发布", False)
            TipWindow(self, f"❌ 图片加载失败: {str(e)}").show()

    def handle_image_processing_error(self, error_msg):
        self.image_label.setPixmap(self.placeholder_photo)
        self.image_title.setText("图片加载失败")
        # 禁用预览发布按钮
        self.update_preview_button("🎯 预览发布", False)
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
            self.current_image_index = (
                self.current_image_index - 1) % len(self.image_list)
            self.show_current_image()

    def next_image(self):
        if self.image_list:
            self.current_image_index = (
                self.current_image_index + 1) % len(self.image_list)
            self.show_current_image()

    def preview_post(self):
        try:
            if not self.browser_thread.poster:
                TipWindow(self, "❌ 请先登录").show()
                return

            title = self.title_input.text()
            content = self.subtitle_input.toPlainText()

            # 更新预览按钮状态
            self.update_preview_button("⏳ 发布中...", False)

            # 添加预览任务到浏览器线程
            self.browser_thread.action_queue.append({
                'type': 'preview',
                'title': title,
                'content': content,
                'images': self.images
            })

        except Exception as e:
            TipWindow(self, f"❌ 预览发布失败: {str(e)}").show()

    def handle_preview_result(self):
        # 恢复预览按钮状态
        self.update_preview_button("🎯 预览发布", True)
        TipWindow(self, "🎉 文章已准备好，请在浏览器中检查并发布").show()

    def handle_preview_error(self, error_msg):
        # 恢复预览按钮状态
        self.update_preview_button("🎯 预览发布", True)
        TipWindow(self, f"❌ 预览发布失败: {error_msg}").show()

    def switch_page(self, index):
        # 切换页面
        self.stack.setCurrentIndex(index)

        # 更新按钮状态
        sidebar = self.findChild(QWidget, "sidebar")
        if sidebar:
            buttons = [btn for btn in sidebar.findChildren(QPushButton)]
            for i, btn in enumerate(buttons):
                btn.setChecked(i == index)

    def update_title_config(self):
        """更新标题配置"""
        try:
            title_config = self.config.get_title_config()
            title_config['title'] = self.header_input.text()
            self.config.update_title_config(title_config['title'])
        except Exception as e:
            self.logger.error(f"更新标题配置失败: {str(e)}")

    def update_author_config(self):
        """更新作者配置"""
        try:
            title_config = self.config.get_title_config()
            title_config['author'] = self.author_input.text()
            self.config.update_author_config(title_config['author'])
        except Exception as e:
            self.logger.error(f"更新作者配置失败: {str(e)}")

    def closeEvent(self, event):
        print("关闭应用")
        try:
            # 停止所有线程
            if hasattr(self, 'browser_thread'):
                self.browser_thread.stop()
                self.browser_thread.wait(1000)  # 等待最多1秒
                if self.browser_thread.isRunning():
                    self.browser_thread.terminate()  # 强制终止
                    self.browser_thread.wait()  # 等待终止完成

            if hasattr(self, 'generator_thread') and self.generator_thread.isRunning():
                self.generator_thread.terminate()
                self.generator_thread.wait()

            if hasattr(self, 'image_processor') and self.image_processor.isRunning():
                self.image_processor.terminate()
                self.image_processor.wait()

            # 关闭浏览器
            if hasattr(self, 'browser_thread') and self.browser_thread.poster:
                try:
                    self.browser_thread.poster.close(force=True)
                except:
                    pass  # 忽略关闭浏览器时的错误

            # 清理资源
            self.images = []
            self.image_list = []
            self.current_image_index = 0

            # 调用父类的closeEvent
            super().closeEvent(event)

        except Exception as e:
            print(f"关闭应用程序时出错: {str(e)}")
            # 即使出错也强制关闭
            event.accept()


if __name__ == "__main__":
    try:
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
    except Exception as e:
        logging.exception("程序运行出错：")
        raise

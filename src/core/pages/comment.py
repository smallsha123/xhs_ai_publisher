import sys

from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QWidget)

from src.core.alert import TipWindow


class CommentPage(QWidget):
    """主页类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        # 初始化变量
        self.images = []
        self.image_list = []
        self.current_image_index = 0
        # 创建占位图
        self.placeholder_photo = QPixmap(200, 200)
        self.placeholder_photo.fill(QColor('#f8f9fa'))

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)

        # 创建登录区域
        self.create_login_section(layout)

        # 创建内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        layout.addLayout(content_layout)

    def create_login_section(self, parent_layout):
        """创建登录区域"""
        login_frame = QFrame()
        login_frame.setStyleSheet("""
            QFrame {
                padding: 8px;
                background-color: white;
            }
            QLabel {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 12pt;
                border: none;
                background: transparent;
            }
            QLineEdit {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 12pt;
            }
            QPushButton {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 12pt;
            }
        """)
        login_layout = QVBoxLayout(login_frame)
        login_layout.setContentsMargins(8, 8, 8, 8)
        login_layout.setSpacing(8)

        # 创建水平布局用于登录控件
        login_controls = QHBoxLayout()
        login_controls.setSpacing(8)

        # 手机号输入
        login_controls.addWidget(QLabel("📱 手机号:"))
        self.phone_input = QLineEdit()
        self.phone_input.setFixedWidth(180)
        self.phone_input.setText(self.parent.config.get_phone_config())
        self.phone_input.textChanged.connect(self.update_phone_config)
        login_controls.addWidget(self.phone_input)

        # 登录按钮
        login_btn = QPushButton("🚀 登录")
        login_btn.setObjectName("zhu_login_btn")
        login_btn.setFixedWidth(100)
        login_btn.clicked.connect(self.login)
        login_controls.addWidget(login_btn)

        # 添加免责声明
        disclaimer_label = QLabel("仅限于学习,请勿用于其他用途,否则后果自负")
        disclaimer_label.setStyleSheet("""
            color: #e74c3c;
            font-size: 11pt;
            font-weight: bold;
        """)
        login_controls.addWidget(disclaimer_label)

        login_controls.addStretch()
        login_layout.addLayout(login_controls)
        parent_layout.addWidget(login_frame)

    def login(self):
        try:
            phone = self.phone_input.text()

            if not phone:
                TipWindow(self.parent, "❌ 请输入手机号").show()
                return

            # 更新登录按钮状态
            self.parent.update_comment_login_button("⏳ 登录中...", False)

            # 添加登录任务到浏览器线程
            self.parent.comment_browser_thread.action_queue.append({
                'type': 'comment',
                'phone': phone
            })

        except Exception as e:
            TipWindow(self.parent, f"❌ 登录失败: {str(e)}").show()

    def handle_login_error(self, error_msg):
        # 恢复登录按钮状态
        self.parent.update_comment_login_button("🚀 登录", True)
        TipWindow(self.parent, f"❌ 登录失败: {error_msg}").show()

    def update_phone_config(self):
        """更新手机号配置"""
        try:
            new_phone = self.phone_input.text()
            self.parent.config.update_phone_config(new_phone)
        except Exception as e:
            self.parent.logger.error(f"更新手机号配置失败: {str(e)}")
            
    def handle_poster_ready(self):
            """处理登录成功后的poster对象"""
            # 更新登录按钮状态
            self.parent.update_comment_login_button("✅ 已登录", False)
            TipWindow(self.parent, "✅ 登录成功").show()
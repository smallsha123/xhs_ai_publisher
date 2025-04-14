import base64
import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

import requests
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QScrollArea, QTextEdit, QVBoxLayout, QWidget,
                             QScrollArea, QGridLayout, QFileDialog, QInputDialog,
                             QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt, QByteArray, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

from src.core.alert import TipWindow
from src.database.group import GroupManager


class VideoProcessThread(QThread):
    """视频处理线程"""
    finished = pyqtSignal(dict)  # 处理完成信号
    error = pyqtSignal(str)      # 处理错误信号
    progress = pyqtSignal(str)   # 进度信号

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.loop = None

    def run(self):
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            self.progress.emit("正在解析视频链接...")
            # 调用API
            server = "http://127.0.0.1:8000/xhs/"
            data = {
                "url": self.url,
                "download": True,
                "index": [3, 6, 9]
            }

            # 发送请求并处理结果
            self.progress.emit("正在获取视频信息...")
            response = requests.post(server, json=data)
            result = response.json()
            
            if 'data' in result:
                self.progress.emit("解析完成，正在处理数据...")
                self.finished.emit(result['data'])
            else:
                raise Exception(result.get('message', '未知错误'))

        except Exception as e:
            self.error.emit(str(e))
        finally:
            # 关闭事件循环
            if self.loop:
                self.loop.close()

class DownloadThread(QThread):
    """下载线程"""
    finished = pyqtSignal(str)  # 下载完成信号
    error = pyqtSignal(str)     # 下载错误信号
    progress = pyqtSignal(str)  # 下载进度信号

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            response = requests.get(self.url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.xiaohongshu.com/'
            })
            if response.status_code == 200:
                with open(self.save_path, 'wb') as f:
                    f.write(response.content)
                self.finished.emit("✅ 图片已保存")
            else:
                raise Exception(f"下载失败: HTTP {response.status_code}")
        except Exception as e:
            self.error.emit(f"❌ 下载失败: {str(e)}")

class BatchDownloadThread(QThread):
    """批量下载线程"""
    finished = pyqtSignal()     # 全部下载完成信号
    error = pyqtSignal(str)     # 下载错误信号
    progress = pyqtSignal(str)  # 下载进度信号

    def __init__(self, urls, save_dir):
        super().__init__()
        self.urls = urls
        self.save_dir = save_dir

    def run(self):
        for i, url in enumerate(self.urls, 1):
            try:
                filename = f"图片_{i}.jpg"
                file_path = os.path.join(self.save_dir, filename)
                
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://www.xiaohongshu.com/'
                })
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    self.progress.emit(f"✅ 图片_{i} 已保存")
                else:
                    raise Exception(f"下载失败: HTTP {response.status_code}")
            except Exception as e:
                self.error.emit(f"❌ 图片_{i} 下载失败: {str(e)}")
        self.finished.emit()

class ToolsPage(QWidget):
    """工具箱页面类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.media_cache = {}  # 用于缓存已下载的媒体文件
        self.download_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'xhs_images')
        os.makedirs(self.download_path, exist_ok=True)
        self.download_thread = None
        self.batch_download_thread = None
        self.video_process_thread = None
        self.progress_label = None  # 添加进度标签属性
        self.setup_ui()

    def init_groups(self):
        """初始化分组列表，在父类group_manager初始化完成后调用"""
        self.load_groups()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 3, 8, 3)
        content_layout.setSpacing(3)
        
        
        

        # 创建分组管理区域
        group_frame = QFrame()
        group_frame.setObjectName("groupFrame")
        group_frame.setStyleSheet("""
            QFrame#groupFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        group_layout = QVBoxLayout(group_frame)
        
        # 分组管理标题
        group_title = QLabel("分组管理")
        group_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        group_layout.addWidget(group_title)
        
        # 添加分组输入框和按钮
        group_input_layout = QHBoxLayout()
        self.group_input = QTextEdit()
        self.group_input.setPlaceholderText("输入分组名称")
        self.group_input.setMaximumHeight(40)
        self.group_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        add_group_btn = QPushButton("添加分组")
        add_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_group_btn.clicked.connect(self.add_group)
        
        group_input_layout.addWidget(self.group_input)
        group_input_layout.addWidget(add_group_btn)
        group_layout.addLayout(group_input_layout)
        
        # 分组列表
        self.group_list = QVBoxLayout()
        group_layout.addLayout(self.group_list)
        
        # 将分组管理区域添加到主布局
        layout.addWidget(group_frame)

        # 创建视频去水印工具区域
        watermark_frame = QFrame()
        watermark_frame.setStyleSheet("""
            QFrame {
                padding: 8px;
                background-color: white;
                border: none;
                border-radius: 8px;
            }
            QLabel {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 12pt;
                color: #2c3e50;
            }
            QLineEdit {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                padding: 4px;
                font-size: 12pt;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                padding: 6px;
                font-size: 14pt;
                font-weight: bold;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        watermark_layout = QVBoxLayout(watermark_frame)
        watermark_layout.setSpacing(3)
        watermark_layout.setContentsMargins(8, 3, 8, 3)

        # 添加标题
        title_label = QLabel("⚡ 视频平台水印去除工具")
        title_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        """)
        watermark_layout.addWidget(title_label)

        url_input = QTextEdit()
        url_input.setPlaceholderText("请输入平台对应的 URL 地址 ~")
        url_input.setMinimumWidth(600)
        url_input.setFixedHeight(40)  # 设置固定高度为35px
        url_input.setStyleSheet("""
            QTextEdit {
                padding: 4px;  /* 减小内边距 */
                font-size: 12pt;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 600px;
                max-height: 40px;  /* 限制最大高度 */
            }
        """)
        watermark_layout.addWidget(url_input)

        # 处理按钮
        process_btn = QPushButton("⚡ 开始处理")
        process_btn.setStyleSheet("""
            QPushButton {
                padding: 6px;  /* 减小内边距 */
                font-size: 14pt;
                font-weight: bold;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                margin-top: 8px;  /* 减小上边距 */
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        self.url_input = url_input
        self.process_btn = process_btn  # 保存为类属性
        process_btn.clicked.connect(self.process_video)
        watermark_layout.addWidget(process_btn)

        # 在process_btn下方添加进度标签
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                margin-top: 4px;
                border: none;
                padding: 0;
            }
        """)
        watermark_layout.addWidget(self.progress_label)

        # 创建结果展示区域
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            QFrame {
                margin-top: 8px;
                padding: 12px;
                background-color: white;
                border: none;
            }
            QLabel {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                color: #2c3e50;
                border: none;
            }
            QTextEdit {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 11pt;
                line-height: 1.4;
                padding: 8px;
                background-color: white;
                border: none;
            }
        """)
        result_layout = QVBoxLayout(result_frame)
        result_layout.setSpacing(2)  # 减小组件间距
        result_layout.setContentsMargins(0, 0, 0, 0)
        
        # 保存为类属性
        self.result_layout = result_layout

        # 添加结果标题
        result_title = QLabel("📋 解析结果")
        result_title.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #1a1a1a;
            border: none;
            margin-bottom: 5px;  /* 减小下边距 */
        """)
        result_layout.addWidget(result_title)

        # 创建结果文本展示区
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 11pt;
                line-height: 1.5;  /* 减小行高 */
                padding: 10px;  /* 减小内边距 */
                background-color: white;
                border: none;
            }
        """)
        self.result_text.setMinimumHeight(300)  # 减小最小高度
        result_layout.addWidget(self.result_text)

        # 将结果区域添加到水印工具布局中
        watermark_layout.addWidget(result_frame)

        # 将水印工具添加到内容布局
        content_layout.addWidget(watermark_frame)
        content_layout.addStretch()

        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)

        # 将滚动区域添加到工具箱页面
        layout.addWidget(scroll_area)
        

    def process_video(self):
        """处理视频链接"""
        try:
            url = self.url_input.toPlainText().strip()
            if not url:
                TipWindow(self.parent, "❌ 请输入视频URL").show()
                return

            # 更新按钮状态和进度提示
            self.process_btn.setText("⏳ 处理中...")
            self.process_btn.setEnabled(False)
            if self.progress_label is not None:
                self.progress_label.setText("准备处理...")
                self.progress_label.setStyleSheet("""
                    QLabel {
                        color: #4a90e2;
                        font-size: 12px;
                        margin-top: 4px;
                        border: none;
                        padding: 0;
                    }
                """)

            # 创建并启动视频处理线程
            self.video_process_thread = VideoProcessThread(url)
            self.video_process_thread.finished.connect(self.handle_video_process_result)
            self.video_process_thread.error.connect(self.handle_video_process_error)
            self.video_process_thread.progress.connect(self.handle_video_process_progress)
            self.video_process_thread.start()

        except Exception as e:
            self.reset_ui_state()
            TipWindow(self.parent, f"❌ 处理失败: {str(e)}").show()

    def handle_video_process_progress(self, message):
        """处理进度更新"""
        if self.progress_label is not None:
            self.progress_label.setText(message)

    def reset_ui_state(self):
        """重置UI状态"""
        self.process_btn.setText("⚡ 开始处理")
        self.process_btn.setEnabled(True)
        if self.progress_label is not None:
            self.progress_label.setText("")
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 12px;
                    margin-top: 4px;
                    border: none;
                    padding: 0;
                }
            """)

    def handle_video_process_result(self, data):
        """处理视频解析结果"""
        try:
            self.parent.pic_manager.insert_pic(data['作品链接'], str(data), 1, int(time.time()))
            # 清空之前的结果
            self.clear_result_area()

            # 创建媒体预览区域
            preview_frame = QFrame()
            preview_frame.setStyleSheet("""
                QFrame {
                    margin-top: 5px;
                    padding: 8px;
                    background-color: white;
                    border: none;
                }
            """)
            preview_layout = QVBoxLayout(preview_frame)
            preview_layout.setSpacing(5)
            preview_layout.setContentsMargins(0, 0, 0, 0)

            # 添加预览标题和按钮区域
            title_bar = QWidget()
            title_layout = QHBoxLayout(title_bar)
            title_layout.setContentsMargins(0, 0, 0, 4)
            title_layout.setSpacing(4)

            title_label = QLabel("图片内容")
            title_label.setStyleSheet("""
                font-size: 14pt;
                font-weight: bold;
                color: #1a1a1a;
                border: none;
                padding: 0;
            """)
            title_layout.addWidget(title_label)

            title_layout.addStretch()

            # 添加下载全部按钮
            download_btn = QPushButton("⬇️ 下载全部")
            download_btn.setStyleSheet("""
                QPushButton {
                    padding: 4px 8px;
                    font-size: 12px;
                    background-color: #4a90e2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #357abd;
                }
            """)
            download_btn.clicked.connect(lambda: self.download_all_images(data['下载地址']))
            title_layout.addWidget(download_btn)

            preview_layout.addWidget(title_bar)

            # 创建图片容器
            images_widget = QWidget()
            images_layout = QVBoxLayout(images_widget)
            images_layout.setSpacing(4)
            images_layout.setContentsMargins(0, 0, 0, 0)

            # 创建图片网格容器
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(4)
            grid_layout.setContentsMargins(0, 0, 0, 0)

            # 加载图片
            if '下载地址' in data:
                row = 0
                col = 0
                for url in data['下载地址']:
                    try:
                        # 创建图片卡片
                        image_card = QFrame()
                        image_card.setFixedSize(150, 230)
                        image_card.setStyleSheet("""
                            QFrame {
                                background-color: white;
                                margin: 0;
                                padding: 0;
                            }
                        """)
                        card_layout = QVBoxLayout(image_card)
                        card_layout.setContentsMargins(0, 0, 0, 0)
                        card_layout.setSpacing(0)

                        # 加载图片
                        response = requests.get(url, headers={
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Referer': 'https://www.xiaohongshu.com/'
                        })
                        image_data = response.content

                        # 创建QPixmap并设置图片
                        pixmap = QPixmap()
                        byte_array = QByteArray(image_data)
                        pixmap.loadFromData(byte_array)

                        if pixmap.isNull():
                            raise Exception("图片加载失败")

                        # 调整图片大小并保持比例
                        image_label = QLabel()
                        image_label.setFixedSize(150, 200)
                        image_label.setStyleSheet("""
                            QLabel {
                                border: none;
                                padding: 0;
                                margin: 0;
                                background: transparent;
                            }
                        """)
                        scaled_pixmap = pixmap.scaled(150, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        card_layout.addWidget(image_label)

                        # 添加下载按钮
                        download_link = QPushButton("下载图片")
                        download_link.setFixedHeight(20)
                        download_link.setCursor(Qt.CursorShape.PointingHandCursor)
                        download_link.setStyleSheet("""
                            QPushButton {
                                color: #4a90e2;
                                border: none;
                                background: none;
                                text-align: center;
                                padding: 0;
                                margin: 0;
                                font-size: 12px;
                            }
                            QPushButton:hover {
                                text-decoration: underline;
                            }
                        """)
                        download_link.clicked.connect(lambda checked, u=url, i=col+1: self.download_image(u, f"图片_{i}.jpg"))
                        card_layout.addWidget(download_link)

                        # 添加到网格布局
                        grid_layout.addWidget(image_card, row, col)
                        col += 1
                        if col >= 4:  # 每行最多显示4个图片
                            col = 0
                            row += 1

                    except Exception as e:
                        print(f"加载图片失败: {str(e)}")
            else:
                # 显示无图片提示
                no_image_label = QLabel("暂无可下载的媒体文件")
                no_image_label.setStyleSheet("""
                    color: #666666;
                    border: none;
                    padding: 0;
                    margin: 0;
                """)
                grid_layout.addWidget(no_image_label, 0, 0)

            images_layout.addWidget(grid_widget)
            preview_layout.addWidget(images_widget)

            # 将预览区域添加到主布局
            self.result_layout.addWidget(preview_frame)

            # 添加作品信息
            self.add_section("🎥 作品信息", [
                ("标题", data.get('作品标题', 'N/A')),
                ("描述", data.get('作品描述', 'N/A')),
                ("类型", data.get('作品类型', 'N/A')),
                ("发布时间", data.get('发布时间', 'N/A'))
            ])

            # 添加创作者信息
            self.add_section("👤 创作者信息", [
                ("昵称", data.get('作者昵称', 'N/A')),
                ("ID", data.get('作者ID', 'N/A'))
            ])

            # 添加数据统计
            stats_frame = QFrame()
            stats_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    padding: 4px;
                    border: none;
                    margin-bottom: 4px;
                }
            """)
            stats_layout = QHBoxLayout(stats_frame)
            stats_layout.setSpacing(0)
            stats_layout.setContentsMargins(2, 1, 2, 1)

            stats = [
                ("👍", data.get('点赞数量', 'N/A')),
                ("⭐", data.get('收藏数量', 'N/A')), 
                ("💬", data.get('评论数量', 'N/A')),
                ("🔄", data.get('分享数量', 'N/A'))
            ]

            for i, (label, value) in enumerate(stats):
                stat_widget = QWidget()
                stat_layout = QHBoxLayout(stat_widget)
                stat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                label_label = QLabel(f"{label} {value}")
                label_label.setStyleSheet("color: #666666; font-size: 12px;")
                stat_layout.addWidget(label_label)

                stats_layout.addWidget(stat_widget)

                if i < len(stats) - 1:
                    divider = QLabel("|")
                    divider.setStyleSheet("color: #e1e4e8;")
                    stats_layout.addWidget(divider)

            self.result_layout.addWidget(stats_frame)

            # 添加标签
            self.add_section("🏷️ 标签", [
                ("", data.get('作品标签', 'N/A'))
            ])

            # 添加链接
            links_frame = QFrame()
            links_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    padding: 8px;
                    border: none;
                    margin-bottom: 8px;
                }
            """)
            links_layout = QVBoxLayout(links_frame)
            links_layout.setSpacing(2)
            links_layout.setContentsMargins(8, 4, 8, 4)

            work_link = QLabel(f"作品链接：<a href='{data.get('作品链接', '#')}' style='color: #4a90e2;'>{data.get('作品链接', 'N/A')}</a>")
            work_link.setOpenExternalLinks(True)
            work_link.setStyleSheet("""
                margin-bottom: 2px;
                border: none;
                padding: 0;
            """)
            links_layout.addWidget(work_link)

            author_link = QLabel(f"作者主页：<a href='{data.get('作者链接', '#')}' style='color: #4a90e2;'>{data.get('作者链接', 'N/A')}</a>")
            author_link.setOpenExternalLinks(True)
            author_link.setStyleSheet("""
                border: none;
                padding: 0;
            """)
            links_layout.addWidget(author_link)

            self.result_layout.addWidget(links_frame)

            # 显示成功提示
            TipWindow(self.parent, "✅ 解析成功").show()

        except Exception as e:
            print("处理视频结果时出错:", str(e))
            error_frame = QFrame()
            error_frame.setStyleSheet("""
                QFrame {
                    background-color: #fee2e2;
                    padding: 8px;
                    border: none;
                    margin: 8px 0;
                }
            """)
            error_layout = QVBoxLayout(error_frame)

            error_title = QLabel("❌ 处理出错")
            error_title.setStyleSheet("color: #dc2626; font-weight: bold;")
            error_layout.addWidget(error_title)

            error_message = QLabel(str(e))
            error_message.setStyleSheet("color: #7f1d1d; margin-top: 5px;")
            error_layout.addWidget(error_message)

            self.result_layout.addWidget(error_frame)
            TipWindow(self.parent, f"❌ 处理失败: {str(e)}").show()

        finally:
            # 重置UI状态
            self.reset_ui_state()

    def handle_video_process_error(self, error_message):
        """处理视频解析错误"""
        self.reset_ui_state()
        TipWindow(self.parent, f"❌ 处理失败: {error_message}").show()

    def clear_result_area(self):
        """清空结果区域"""
        # 清空结果布局中的所有组件
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 重新添加结果标题
        result_title = QLabel("📋 解析结果")
        result_title.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #1a1a1a;
            border: none;
            margin-bottom: 5px;
        """)
        self.result_layout.addWidget(result_title)

    def add_section(self, title, items):
        """添加一个信息区块"""
        section_frame = QFrame()
        section_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                margin-bottom: 8px;
            }
        """)
        section_layout = QVBoxLayout(section_frame)
        section_layout.setSpacing(2)
        section_layout.setContentsMargins(8, 4, 8, 4)
        
        # 添加标题
        section_title = QLabel(title)
        section_title.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 4px;
            border: none;
        """)
        section_layout.addWidget(section_title)
        
        # 添加内容
        for label, value in items:
            if label:
                item_layout = QHBoxLayout()
                item_layout.setSpacing(4)
                label_widget = QLabel(f"{label}:")
                label_widget.setStyleSheet("""
                    color: #666666;
                    border: none;
                    padding: 0;
                """)
                item_layout.addWidget(label_widget)
                
                value_widget = QLabel(value)
                value_widget.setStyleSheet("""
                    color: #1a1a1a;
                    border: none;
                    padding: 0;
                """)
                item_layout.addWidget(value_widget)
                item_layout.addStretch()
                
                section_layout.addLayout(item_layout)
            else:
                value_widget = QLabel(value)
                value_widget.setStyleSheet("""
                    color: #4a90e2;
                    border: none;
                    padding: 0;
                """)
                section_layout.addWidget(value_widget)
        
        self.result_layout.addWidget(section_frame)

    def create_media_preview_html(self, urls):
        """创建媒体预览的HTML"""
        if not urls:
            return "<div style='color: #666666;'>暂无可下载的媒体文件</div>"

        # 图片网格布局
        preview_html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; margin-bottom: 20px;'>"

        # 创建线程池
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有图片加载任务
            future_to_url = {executor.submit(self.load_image, url): url for url in urls}

            # 处理完成的任务
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result['success']:
                        preview_html += f"""
                        <div style='
                            background-color: white;
                            border: 1px solid #e1e4e8;
                            border-radius: 8px;
                            overflow: hidden;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        '>
                            <div style='position: relative; padding-top: 75%; overflow: hidden;'>
                                <img src="{result['data']}" style='
                                    position: absolute;
                                    top: 0;
                                    left: 0;
                                    width: 100%;
                                    height: 100%;
                                    object-fit: cover;
                                ' loading="lazy">
                            </div>
                            <div style='padding: 8px; text-align: center;'>
                                <a href="{url}" style='
                                    color: #4a90e2;
                                    text-decoration: none;
                                    font-size: 14px;
                                ' target="_blank">下载图片</a>
                            </div>
                        </div>
                        """
                    else:
                        preview_html += f"""
                        <div style='
                            background-color: white;
                            border: 1px solid #e1e4e8;
                            border-radius: 8px;
                            padding: 15px;
                            text-align: center;
                        '>
                            <div style='color: #666666; margin-bottom: 8px;'>图片加载失败</div>
                            <a href="{url}" style='color: #4a90e2; text-decoration: none;' target="_blank">下载图片</a>
                        </div>
                        """
                except Exception as e:
                    print(f"处理图片结果时出错: {str(e)}")
                    preview_html += f"""
                    <div style='
                        background-color: white;
                        border: 1px solid #e1e4e8;
                        border-radius: 8px;
                        padding: 15px;
                        text-align: center;
                    '>
                        <div style='color: #666666; margin-bottom: 8px;'>处理图片时出错</div>
                        <a href="{url}" style='color: #4a90e2; text-decoration: none;' target="_blank">下载图片</a>
                    </div>
                    """

        preview_html += "</div>"
        return preview_html

    def fill_example_url(self, url):
        """填充示例URL"""
        self.url_input.setText(url)
        TipWindow(self.parent, "已填充示例链接，请替换为实际链接").show()

    def load_image(self, url):
        """加载单个图片"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.xiaohongshu.com/'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            content_type = response.headers.get('content-type', 'image/jpeg')
            image_data = base64.b64encode(response.content).decode('utf-8')
            return {
                'success': True,
                'url': url,
                'data': f"data:{content_type};base64,{image_data}"
            }
        except Exception as e:
            print(f"加载图片失败: {str(e)}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }

    def download_image(self, url, filename):
        """下载单个图片"""
        # 让用户选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择保存位置",
            filename,
            "图片文件 (*.jpg *.png)"
        )
        
        if not file_path:  # 用户取消了选择
            return
            
        # 创建并启动下载线程
        self.download_thread = DownloadThread(url, file_path)
        self.download_thread.finished.connect(self.handle_download_finished)
        self.download_thread.error.connect(self.handle_download_error)
        self.download_thread.start()

    def download_all_images(self, urls):
        """下载所有图片"""
        # 让用户选择保存目录
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            os.path.expanduser('~')
        )
        
        if not save_dir:  # 用户取消了选择
            return
            
        # 创建并启动批量下载线程
        self.batch_download_thread = BatchDownloadThread(urls, save_dir)
        self.batch_download_thread.finished.connect(self.handle_batch_download_finished)
        self.batch_download_thread.error.connect(self.handle_download_error)
        self.batch_download_thread.progress.connect(self.handle_download_progress)
        self.batch_download_thread.start()

    def handle_download_finished(self, message):
        """处理单个下载完成"""
        TipWindow(self.parent, message).show()

    def handle_batch_download_finished(self):
        """处理批量下载完成"""
        TipWindow(self.parent, "✅ 所有图片下载完成").show()

    def handle_download_error(self, error_message):
        """处理下载错误"""
        TipWindow(self.parent, error_message).show()

    def handle_download_progress(self, message):
        """处理下载进度"""
        TipWindow(self.parent, message).show()

    def load_groups(self):
        """加载分组列表"""
        # 清空现有分组列表
        while self.group_list.count():
            item = self.group_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 创建网格布局容器
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(8)  # 减小网格间距
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # 获取所有分组
        groups = self.parent.group_manager.get_all_groups()
        
        # 添加分组到网格
        row = 0
        col = 0
        max_cols = 3  # 每行最多显示3个分组
        
        for group in groups:
            # 创建分组卡片
            group_card = QFrame()
            group_card.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 12px;
                }
                QFrame:hover {
                    background-color: #e9ecef;
                }
            """)
            
            # 创建卡片布局
            card_layout = QVBoxLayout(group_card)
            card_layout.setSpacing(6)  # 减小卡片内部间距
            card_layout.setContentsMargins(8, 8, 8, 8)  # 减小卡片内边距
            
            # 添加公司图标和名称布局
            header_layout = QHBoxLayout()
            header_layout.setSpacing(8)  # 减小头部布局间距
            
            # 公司图标
            icon_label = QLabel()
            icon_label.setFixedSize(32, 32)  # 减小图标尺寸
            icon_label.setStyleSheet("""
                background-color: white;
                border-radius: 16px;
                padding: 6px;
            """)
            header_layout.addWidget(icon_label)
            
            # 公司信息布局
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)  # 减小信息布局间距
            
            # 公司名称
            name_label = QLabel(str(group[1]))
            name_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #333;
            """)
            info_layout.addWidget(name_label)
            
            header_layout.addLayout(info_layout)
            header_layout.addStretch()
            card_layout.addLayout(header_layout)
            
            # 添加创建时间
            time_label = QLabel(f"创建时间：{datetime.fromtimestamp(group[2]).strftime('%Y-%m-%d %H:%M:%S')}")
            time_label.setStyleSheet("""
                font-size: 11px;
                color: #999;
                margin-top: 4px;
            """)
            card_layout.addWidget(time_label)
            
            # 添加按钮布局
            button_layout = QHBoxLayout()
            button_layout.setSpacing(6)  # 减小按钮间距
            
            # 编辑按钮
            edit_btn = QPushButton("编辑")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #2196F3;
                    border: 1px solid #2196F3;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2196F3;
                    color: white;
                }
            """)
            edit_btn.clicked.connect(lambda checked, g=group: self.edit_group(g))
            button_layout.addWidget(edit_btn)
            
            # 删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #f44336;
                    border: 1px solid #f44336;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #f44336;
                    color: white;
                }
            """)
            delete_btn.clicked.connect(lambda checked, g=group: self.delete_group(g))
            button_layout.addWidget(delete_btn)
            
            card_layout.addLayout(button_layout)
            
            # 添加到网格布局
            grid_layout.addWidget(group_card, row, col)
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(grid_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 将滚动区域添加到分组列表布局
        self.group_list.addWidget(scroll_area)

    def add_group(self):
        """添加新分组"""
        group_name = self.group_input.toPlainText().strip()
        if not group_name:
            return
            
        try:
            self.parent.group_manager.insert_group(group_name, int(time.time()))
            self.group_input.clear()
            self.load_groups()
        except Exception as e:
            print(f"添加分组失败: {e}")

    def edit_group(self, group):
        """编辑分组"""
        new_name, ok = QInputDialog.getText(
            self,
            "编辑分组",
            "请输入新的分组名称:",
            QLineEdit.EchoMode.Normal,
            str(group[1])
        )
        
        if ok and new_name.strip():
            try:
                self.parent.group_manager.update_group_name(group[0], new_name.strip())
                self.load_groups()
            except Exception as e:
                print(f"编辑分组失败: {e}")

    def delete_group(self, group):
        """删除分组"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除分组 '{group[1]}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.parent.group_manager.delete_group(group[0])
                self.load_groups()
            except Exception as e:
                print(f"删除分组失败: {e}")

import base64
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from PIL import Image

import requests
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QScrollArea, QTextEdit, QVBoxLayout, QWidget,
                             QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap, QImage

from src.core.alert import TipWindow


class ToolsPage(QWidget):
    """工具箱页面类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.media_cache = {}  # 用于缓存已下载的媒体文件

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
        content_layout.setContentsMargins(8, 3, 8, 3)  # 减小外边距
        content_layout.setSpacing(3)  # 减小组件间距

        # 创建视频去水印工具区域
        watermark_frame = QFrame()
        watermark_frame.setStyleSheet("""
            QFrame {
                padding: 8px;  /* 减小内边距 */
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
                padding: 4px;  /* 减小输入框内边距 */
                font-size: 12pt;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                padding: 6px;  /* 减小按钮内边距 */
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
        watermark_layout = QVBoxLayout(watermark_frame)
        watermark_layout.setSpacing(3)  # 减小组件间距
        watermark_layout.setContentsMargins(8, 3, 8, 3)  # 减小内边距

        # 添加标题
        title_label = QLabel("⚡ 视频平台水印去除工具")
        title_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;  /* 减小下边距 */
        """)
        watermark_layout.addWidget(title_label)

        url_input = QTextEdit()
        url_input.setPlaceholderText("请输入平台对应的 URL 地址 ~")
        url_input.setMinimumWidth(600)
        url_input.setMinimumHeight(50)  # 减小高度
        url_input.setStyleSheet("""
            QTextEdit {
                padding: 4px;  /* 减小内边距 */
                font-size: 12pt;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 600px;
                min-height: 50px;  /* 减小最小高度 */
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
        process_btn.clicked.connect(self.process_video)
        watermark_layout.addWidget(process_btn)

        # 创建结果展示区域
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            QFrame {
                margin-top: 8px;  /* 减小上边距 */
                padding: 12px;  /* 减小内边距 */
                background-color: white;
                border: 1px solid #e1e4e8;
                border-radius: 12px;
            }
            QLabel {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                color: #2c3e50;
            }
            QTextEdit {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 11pt;
                line-height: 1.4;  /* 减小行高 */
                padding: 8px;  /* 减小内边距 */
                background-color: white;
                border: none;
                border-radius: 8px;
            }
            QLabel#section_header {
                font-size: 14pt;
                font-weight: bold;
                color: #1a1a1a;
                padding: 2px 0;  /* 减小内边距 */
                margin-top: 3px;  /* 减小上边距 */
            }
            QLabel#section_content {
                font-size: 12pt;
                color: #666666;
                padding: 1px 0;  /* 减小内边距 */
            }
            QLabel#section_divider {
                background-color: #f5f5f5;
                min-height: 1px;
                margin: 3px 0;  /* 减小外边距 */
            }
            QLabel#download_link {
                color: #4a90e2;
                text-decoration: underline;
                cursor: pointer;
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
        try:
            url = self.url_input.toPlainText().strip()
            if not url:
                TipWindow(self.parent, "❌ 请输入视频URL").show()
                return

            # 调用API
            server = "http://127.0.0.1:8000/xhs/"
            data = {
                "url": url,
                "download": True,
                "index": [3, 6, 9]
            }

            # 发送请求并处理结果
            response = requests.post(server, json=data)
            result = response.json()

            # 清空之前的结果
            self.clear_result_area()

            # 格式化显示结果
            if 'data' in result:
                data = result['data']
                
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
                title_layout.setContentsMargins(0, 0, 0, 5)
                title_layout.setSpacing(5)
                
                title_label = QLabel("图片内容")
                title_label.setStyleSheet("""
                    font-size: 16pt;
                    font-weight: bold;
                    color: #1a1a1a;
                """)
                title_layout.addWidget(title_label)
                
                title_layout.addStretch()
                
                watermark_btn = QPushButton("📝 图片加水印")
                watermark_btn.setStyleSheet("""
                    QPushButton {
                        padding: 4px 8px;
                        font-size: 12pt;
                        background-color: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        margin-right: 5px;
                    }
                    QPushButton:hover {
                        background-color: #357abd;
                    }
                """)
                title_layout.addWidget(watermark_btn)
                
                download_btn = QPushButton("⬇️ 下载全部")
                download_btn.setStyleSheet("""
                    QPushButton {
                        padding: 4px 8px;
                        font-size: 12pt;
                        background-color: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #357abd;
                    }
                """)
                title_layout.addWidget(download_btn)
                
                preview_layout.addWidget(title_bar)
                
                # 创建图片预览滚动区域
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                scroll_area.setStyleSheet("""
                    QScrollArea {
                        border: none;
                        background-color: transparent;
                    }
                    QScrollBar:horizontal {
                        height: 6px;
                        background: transparent;
                    }
                    QScrollBar::handle:horizontal {
                        background: #888;
                        min-width: 20px;
                        border-radius: 3px;
                    }
                    QScrollBar::add-line:horizontal {
                        width: 0px;
                    }
                    QScrollBar::sub-line:horizontal {
                        width: 0px;
                    }
                """)
                
                # 创建图片容器
                images_widget = QWidget()
                images_layout = QHBoxLayout(images_widget)
                images_layout.setSpacing(5)
                images_layout.setContentsMargins(0, 0, 0, 0)
                
                # 加载图片
                if 'download_urls' in data:
                    for url in data['download_urls']:
                        try:
                            # 创建图片卡片
                            image_card = QFrame()
                            image_card.setFixedSize(150, 180)  # 进一步减小卡片大小
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
                            pixmap.loadFromData(QByteArray(image_data))
                            
                            # 调整图片大小并保持比例
                            image_label = QLabel()
                            image_label.setFixedSize(150, 150)  # 减小图片大小
                            image_label.setStyleSheet("""
                                QLabel {
                                    border: none;
                                    padding: 0;
                                    margin: 0;
                                    background: transparent;
                                }
                            """)
                            scaled_pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            image_label.setPixmap(scaled_pixmap)
                            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            card_layout.addWidget(image_label)
                            
                            # 添加下载按钮
                            download_link = QPushButton("下载图片")
                            download_link.setFixedHeight(20)  # 设置固定高度
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
                            card_layout.addWidget(download_link)
                            
                            # 添加到布局
                            images_layout.addWidget(image_card)
                            
                        except Exception as e:
                            print(f"加载图片失败: {str(e)}")
                
                images_layout.addStretch()
                scroll_area.setWidget(images_widget)
                preview_layout.addWidget(scroll_area)
                
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
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }
                """)
                stats_layout = QHBoxLayout(stats_frame)
                stats_layout.setSpacing(0)
                
                stats = [
                    ("👍 点赞", data.get('点赞数量', 'N/A')),
                    ("⭐ 收藏", data.get('收藏数量', 'N/A')),
                    ("💬 评论", data.get('评论数量', 'N/A')),
                    ("🔄 分享", data.get('分享数量', 'N/A'))
                ]
                
                for i, (label, value) in enumerate(stats):
                    stat_widget = QWidget()
                    stat_layout = QVBoxLayout(stat_widget)
                    stat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    value_label = QLabel(value)
                    value_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #1a1a1a;")
                    stat_layout.addWidget(value_label)
                    
                    label_label = QLabel(label)
                    label_label.setStyleSheet("color: #666666;")
                    stat_layout.addWidget(label_label)
                    
                    stats_layout.addWidget(stat_widget)
                    
                    if i < len(stats) - 1:
                        divider = QFrame()
                        divider.setFrameShape(QFrame.Shape.VLine)
                        divider.setStyleSheet("background-color: #e1e4e8;")
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
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }
                """)
                links_layout = QVBoxLayout(links_frame)
                
                work_link = QLabel(f"作品链接：<a href='{data.get('作品链接', '#')}' style='color: #4a90e2;'>{data.get('作品链接', 'N/A')}</a>")
                work_link.setOpenExternalLinks(True)
                work_link.setStyleSheet("margin-bottom: 5px;")
                links_layout.addWidget(work_link)
                
                author_link = QLabel(f"作者主页：<a href='{data.get('作者链接', '#')}' style='color: #4a90e2;'>{data.get('作者链接', 'N/A')}</a>")
                author_link.setOpenExternalLinks(True)
                links_layout.addWidget(author_link)
                
                self.result_layout.addWidget(links_frame)

                # 显示成功提示
                TipWindow(self.parent, "✅ 解析成功").show()
            else:
                error_frame = QFrame()
                error_frame.setStyleSheet("""
                    QFrame {
                        background-color: #fee2e2;
                        padding: 15px;
                        border-radius: 8px;
                        margin: 10px 0;
                    }
                """)
                error_layout = QVBoxLayout(error_frame)
                
                error_title = QLabel("❌ 解析失败")
                error_title.setStyleSheet("color: #dc2626; font-weight: bold;")
                error_layout.addWidget(error_title)
                
                error_message = QLabel(result.get('message', '未知错误'))
                error_message.setStyleSheet("color: #7f1d1d; margin-top: 5px;")
                error_layout.addWidget(error_message)
                
                self.result_layout.addWidget(error_frame)
                TipWindow(self.parent, "❌ 解析失败").show()

        except Exception as e:
            print("处理视频时出错:", str(e))
            error_frame = QFrame()
            error_frame.setStyleSheet("""
                QFrame {
                    background-color: #fee2e2;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
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
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
        """)
        section_layout = QVBoxLayout(section_frame)
        
        # 添加标题
        section_title = QLabel(title)
        section_title.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 10px;
        """)
        section_layout.addWidget(section_title)
        
        # 添加内容
        for label, value in items:
            if label:
                item_layout = QHBoxLayout()
                label_widget = QLabel(f"{label}:")
                label_widget.setStyleSheet("color: #666666;")
                item_layout.addWidget(label_widget)
                
                value_widget = QLabel(value)
                value_widget.setStyleSheet("color: #1a1a1a;")
                item_layout.addWidget(value_widget)
                
                section_layout.addLayout(item_layout)
            else:
                value_widget = QLabel(value)
                value_widget.setStyleSheet("color: #4a90e2;")
                section_layout.addWidget(value_widget)
        
        self.result_layout.addWidget(section_frame)

    def create_media_preview_html(self, urls):
        """创建媒体预览的HTML"""
        if not urls:
            return "<div style='color: #666666;'>暂无可下载的媒体文件</div>"

        # 添加标题和按钮区域
        preview_html = """
        <div style='margin-bottom: 15px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                <div style='font-size: 18px; font-weight: bold;'>图片内容</div>
                <div>
                    <button onclick='window.watermarkImages()' style='
                        background-color: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                        margin-right: 10px;
                        cursor: pointer;
                    '>
                        <span style='margin-right: 4px;'>📝</span>图片加水印
                    </button>
                    <button onclick='window.downloadAllImages()' style='
                        background-color: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                        cursor: pointer;
                    '>
                        <span style='margin-right: 4px;'>⬇️</span>下载全部
                    </button>
                </div>
            </div>
        </div>
        """

        # 图片网格布局
        preview_html += "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; margin-bottom: 20px;'>"

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

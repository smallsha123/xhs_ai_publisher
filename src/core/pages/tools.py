import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QFrame,
                             QScrollArea)

from PyQt6.QtGui import QIcon


from src.core.alert import TipWindow

from src.config.constants import VERSION

import requests
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed


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
        content_layout.setContentsMargins(15, 10, 15, 10)
        content_layout.setSpacing(8)

        # 创建视频去水印工具区域
        watermark_frame = QFrame()
        watermark_frame.setStyleSheet("""
            QFrame {
                padding: 15px;
                background-color: white;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
            }
            QLabel {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 12pt;
                color: #2c3e50;
            }
            QLineEdit {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                padding: 8px;
                font-size: 12pt;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                padding: 10px;
                font-size: 14pt;
                font-weight: bold;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        watermark_layout = QVBoxLayout(watermark_frame)

        # 添加标题
        title_label = QLabel("⚡ 视频平台水印去除工具")
        title_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        """)
        watermark_layout.addWidget(title_label)

        # URL输入框
        url_label = QLabel("* 请输入 URL 地址")
        url_label.setStyleSheet("color: #e74c3c; font-size: 12pt;")
        watermark_layout.addWidget(url_label)

        url_input = QLineEdit()
        url_input.setPlaceholderText("请输入平台对应的 URL 地址 ~")
        url_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 12pt;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        watermark_layout.addWidget(url_input)

        # 支持平台说明
        platform_label = QLabel("支持平台列表如下: (可点击图标进行测试)")
        platform_label.setStyleSheet("color: #7f8c8d; margin-top: 15px;")
        watermark_layout.addWidget(platform_label)

        # 平台图标列表
        platform_widget = QWidget()
        platform_layout = QHBoxLayout(platform_widget)
        platform_layout.setSpacing(20)

        platforms = [
            ("快手", "ks.png", "https://v.kuaishou.com/xxxxx"),
            ("皮皮虾", "ppx.png", "https://h5.pipix.com/item/xxxxx"),
            ("抖音", "dy.png", "https://v.douyin.com/xxxxx"),
            ("微视", "ws.png", "https://h5.weibo.cn/xxxxx"),
            ("小红书", "xhs.png", "https://www.xiaohongshu.com/explore/xxxxx"),
            ("最右", "zy.png", "https://share.izuiyou.com/xxxxx")
        ]

        for name, icon, example_url in platforms:
            btn = QPushButton()
            btn.setIcon(QIcon(f"icons/{icon}"))
            btn.setFixedSize(50, 50)
            btn.setToolTip(f"点击填充{name}示例链接")
            btn.clicked.connect(
                lambda checked, url=example_url: self.fill_example_url(url))
            platform_layout.addWidget(btn)

        watermark_layout.addWidget(platform_widget)

        # 处理按钮
        process_btn = QPushButton("⚡ 开始处理")
        process_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 14pt;
                font-weight: bold;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        # 保存url_input为类属性以便在其他方法中访问
        self.url_input = url_input
        # 连接点击事件到处理函数
        process_btn.clicked.connect(self.process_video)
        watermark_layout.addWidget(process_btn)

        # 创建结果展示区域
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            QFrame {
                margin-top: 20px;
                padding: 20px;
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
                line-height: 1.6;
                padding: 15px;
                background-color: white;
                border: none;
                border-radius: 8px;
            }
            QLabel#section_header {
                font-size: 14pt;
                font-weight: bold;
                color: #1a1a1a;
                padding: 5px 0;
                margin-top: 10px;
            }
            QLabel#section_content {
                font-size: 12pt;
                color: #666666;
                padding: 3px 0;
            }
            QLabel#section_divider {
                background-color: #f5f5f5;
                min-height: 1px;
                margin: 10px 0;
            }
            QLabel#download_link {
                color: #4a90e2;
                text-decoration: underline;
                cursor: pointer;
            }
        """)
        result_layout = QVBoxLayout(result_frame)
        result_layout.setSpacing(0)
        result_layout.setContentsMargins(0, 0, 0, 0)

        # 添加结果标题
        result_title = QLabel("📋 解析结果")
        result_title.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        """)
        result_layout.addWidget(result_title)

        # 创建结果文本展示区
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                font-family: """ + ("Menlo" if sys.platform == "darwin" else "Consolas") + """;
                font-size: 11pt;
                line-height: 1.6;
                padding: 15px;
                background-color: white;
                border: none;
            }
        """)
        self.result_text.setMinimumHeight(400)
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
            url = self.url_input.text().strip()
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

            # 格式化显示结果
            if 'data' in result:
                data = result['data']
                # 创建预览区域的HTML
                preview_html = self.create_media_preview_html(
                    data.get('下载地址', []))

                formatted_result = f"""
<h2 style='color: #1a1a1a; margin-bottom: 20px;'>🎥 作品信息</h2>

<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
    <div style='font-size: 14pt; font-weight: bold; color: #1a1a1a; margin-bottom: 10px;'>{data.get('作品标题', 'N/A')}</div>
    <div style='color: #666666; margin-bottom: 5px;'>📝 {data.get('作品描述', 'N/A')}</div>
    <div style='color: #999999; font-size: 10pt;'>
        {data.get('作品类型', 'N/A')} · {data.get('发布时间', 'N/A')}
    </div>
</div>

<h3 style='color: #1a1a1a; margin: 15px 0;'>👤 创作者信息</h3>
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
    <div style='font-weight: bold; color: #1a1a1a;'>{data.get('作者昵称', 'N/A')}</div>
    <div style='color: #666666;'>ID: {data.get('作者ID', 'N/A')}</div>
</div>

<h3 style='color: #1a1a1a; margin: 15px 0;'>📊 数据统计</h3>
<div style='display: flex; align-items: center; background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
    <div style='flex: 1; text-align: center; position: relative;'>
        <div style='display: flex; align-items: center; justify-content: center; gap: 8px;'>
            <span style='font-size: 16pt; font-weight: bold; color: #1a1a1a;'>{data.get('点赞数量', 'N/A')}</span>
            <span style='color: #666666;'>👍 点赞</span>
        </div>
    </div>
    <div style='width: 1px; height: 24px; background-color: #e1e4e8;'></div>
    <div style='flex: 1; text-align: center; position: relative;'>
        <div style='display: flex; align-items: center; justify-content: center; gap: 8px;'>
            <span style='font-size: 16pt; font-weight: bold; color: #1a1a1a;'>{data.get('收藏数量', 'N/A')}</span>
            <span style='color: #666666;'>⭐ 收藏</span>
        </div>
    </div>
    <div style='width: 1px; height: 24px; background-color: #e1e4e8;'></div>
    <div style='flex: 1; text-align: center; position: relative;'>
        <div style='display: flex; align-items: center; justify-content: center; gap: 8px;'>
            <span style='font-size: 16pt; font-weight: bold; color: #1a1a1a;'>{data.get('评论数量', 'N/A')}</span>
            <span style='color: #666666;'>💬 评论</span>
        </div>
    </div>
    <div style='width: 1px; height: 24px; background-color: #e1e4e8;'></div>
    <div style='flex: 1; text-align: center; position: relative;'>
        <div style='display: flex; align-items: center; justify-content: center; gap: 8px;'>
            <span style='font-size: 16pt; font-weight: bold; color: #1a1a1a;'>{data.get('分享数量', 'N/A')}</span>
            <span style='color: #666666;'>🔄 分享</span>
        </div>
    </div>
</div>

<h3 style='color: #1a1a1a; margin: 15px 0;'>🏷️ 标签</h3>
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
    <div style='color: #4a90e2;'>{data.get('作品标签', 'N/A')}</div>
</div>

<h3 style='color: #1a1a1a; margin: 15px 0;'>🔗 链接</h3>
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
    <div style='margin-bottom: 5px;'><span style='color: #666666;'>作品链接：</span><a href='{data.get('作品链接', '#')}' style='color: #4a90e2;'>{data.get('作品链接', 'N/A')}</a></div>
    <div><span style='color: #666666;'>作者主页：</span><a href='{data.get('作者链接', '#')}' style='color: #4a90e2;'>{data.get('作者链接', 'N/A')}</a></div>
</div>

<h3 style='color: #1a1a1a; margin: 15px 0;'>📥 媒体预览</h3>
{preview_html}
"""
                # 更新结果显示
                self.result_text.setHtml(formatted_result)

                # 显示成功提示
                TipWindow(self.parent, "✅ 解析成功").show()
            else:
                error_message = f"""
<div style='background-color: #fee2e2; padding: 15px; border-radius: 8px; margin: 10px 0;'>
    <div style='color: #dc2626; font-weight: bold;'>❌ 解析失败</div>
    <div style='color: #7f1d1d; margin-top: 5px;'>{result.get('message', '未知错误')}</div>
</div>
"""
                self.result_text.setHtml(error_message)
                TipWindow(self.parent, "❌ 解析失败").show()

        except Exception as e:
            print("处理视频时出错:", str(e))
            error_message = f"""
<div style='background-color: #fee2e2; padding: 15px; border-radius: 8px; margin: 10px 0;'>
    <div style='color: #dc2626; font-weight: bold;'>❌ 处理出错</div>
    <div style='color: #7f1d1d; margin-top: 5px;'>{str(e)}</div>
</div>
"""
            self.result_text.setHtml(error_message)
            TipWindow(self.parent, f"❌ 处理失败: {str(e)}").show()

    def create_media_preview_html(self, urls):
        """创建媒体预览的HTML"""
        if not urls:
            return "<div style='color: #666666;'>暂无可下载的媒体文件</div>"

        preview_html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;'>"

        # 创建线程池
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有图片加载任务
            future_to_url = {executor.submit(
                self.load_image, url): url for url in urls}

            # 处理完成的任务
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result['success']:
                        preview_html += f"""
                        <div style='background-color: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;'>
                            <img src="{result['data']}" style='width: 100%; max-width: 300px; border-radius: 4px; object-fit: cover;' loading="lazy">
                            <div style='margin-top: 8px;'>
                                <a href="{url}" style='color: #4a90e2; text-decoration: none;' target="_blank">下载图片</a>
                            </div>
                        </div>
                        """
                    else:
                        preview_html += f"""
                        <div style='background-color: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;'>
                            <div style='color: #666666; margin-bottom: 8px;'>图片加载失败</div>
                            <a href="{url}" style='color: #4a90e2; text-decoration: none;' target="_blank">下载图片</a>
                        </div>
                        """
                except Exception as e:
                    print(f"处理图片结果时出错: {str(e)}")
                    preview_html += f"""
                    <div style='background-color: #f8f9fa; padding: 10px; border-radius: 8px; text-align: center;'>
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

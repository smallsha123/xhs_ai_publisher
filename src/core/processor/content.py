import json
from PyQt6.QtCore import QThread, pyqtSignal

import requests

class ContentGeneratorThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, input_text, header_title, author, generate_btn):
        super().__init__()
        self.input_text = input_text
        self.header_title = header_title
        self.author = author
        self.generate_btn = generate_btn

    def run(self):
        try:
            # 更新按钮状态
            self.generate_btn.setText("⏳ 生成中...")
            self.generate_btn.setEnabled(False)

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
        finally:
            # 恢复按钮状态
            self.generate_btn.setText("✨ 生成内容")
            self.generate_btn.setEnabled(True)
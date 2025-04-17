from PyQt6.QtCore import QThread, pyqtSignal


from src.core.write_xiaohongshu import XiaohongshuPoster
from src.core.comment_xiaohongshu import XiaohongshuComment


class BrowserThread(QThread):
    # 添加信号
    login_status_changed = pyqtSignal(str, bool)  # 用于更新登录按钮状态
    preview_status_changed = pyqtSignal(str, bool)  # 用于更新预览按钮状态
    login_success = pyqtSignal(object)  # 用于传递poster对象
    login_error = pyqtSignal(str)  # 用于传递错误信息
    preview_success = pyqtSignal()  # 用于通知预览成功
    preview_error = pyqtSignal(str)  # 用于传递预览错误信息

    def __init__(self):
        super().__init__()
        self.poster = None
        self.action_queue = []
        self.is_running = True

    def run(self):
        while self.is_running:
            if self.action_queue:
                action = self.action_queue.pop(0)
                try:
                    if action['type'] == 'login':
                        self.poster = XiaohongshuPoster()
                        self.poster.login(action['phone'])
                        self.login_success.emit(self.poster)
                    elif action['type'] == 'preview' and self.poster:
                        self.poster.post_article(
                            action['title'],
                            action['content'],
                            action['images']
                        )
                        self.preview_success.emit()
                    elif action['type'] == 'comment':
                        self.comment = XiaohongshuComment()
                        self.comment.login(action['phone'])
                        self.login_success.emit()    
                        
                        
                except Exception as e:
                    if action['type'] == 'login':
                        self.login_error.emit(str(e))
                    elif action['type'] == 'preview':
                        self.preview_error.emit(str(e))
            self.msleep(100)  # 避免CPU占用过高

    def stop(self):
        self.is_running = False
        if self.poster:
            self.poster.close(force=True)

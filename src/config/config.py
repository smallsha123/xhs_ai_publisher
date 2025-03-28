import json
import os


class Config:
    """配置管理类"""

    def __init__(self):
        # 获取用户主目录
        home_dir = os.path.expanduser('~')
        # 创建应用配置目录
        app_config_dir = os.path.join(home_dir, '.xhs_system')
        if not os.path.exists(app_config_dir):
            os.makedirs(app_config_dir)

        # 配置文件路径
        self.config_file = os.path.join(app_config_dir, 'settings.json')

        self.default_config = {
            "app": "debug",
            "title_edit": {
                "author": "小红书",
                "title": "测试标题",
            }

        }
        self.load_config()

    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self.default_config
                self.save_config()
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            self.config = self.default_config

    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"保存配置失败: {str(e)}")

    def get_app_config(self):
        """获取app配置"""
        return self.config.get('app', self.default_config['app'])

    def update_app_config(self, app):
        """更新app配置"""
        self.config['app'] = app
        self.save_config()

    def get_title_config(self):
        """获取邮箱配置"""
        return self.config.get('title_edit', self.default_config['title_edit'])

    def update_title_config(self, title):
        """更新邮箱配置"""
        self.config['title_edit']['title'] = title
        self.save_config()

    def update_author_config(self, author):
        """更新邮箱配置"""
        self.config['title_edit'][author] = author
        self.save_config()

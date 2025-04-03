import sys
import os
from rich import print as rprint

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.write_xiaohongshu import XiaohongshuPoster



def test_xiaohongshu():
    # 获取项目根目录
    poster = XiaohongshuPoster()
    # phone = input("请输入手机号: ")
    phone = 15239851762
    poster.login(phone)
    
    rprint("登录成功")
    rprint("开始发布文章")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    poster.post_article("测试标题", "测试内容", [os.path.join(project_root, "images/mp_qr.jpg")])
    poster.close()
    

if __name__ == "__main__":
    test_xiaohongshu()

# 小红书的自动发稿
from playwright.sync_api import sync_playwright
import time
import json
import os
import sys
import logging
log_path = os.path.expanduser('~/Desktop/xhsai_error.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG)

class XiaohongshuPoster:
    def __init__(self):
        try:
            print("开始初始化Playwright...")
            self.playwright = sync_playwright().start()

            # 获取可执行文件所在目录
            launch_args = {
                'headless': False,
                'args': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-infobars',
                    '--start-maximized',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors'
                ]
            }

            chromium_path = None

            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                executable_dir = os.path.dirname(sys.executable)
                print(f"executable_dir: {executable_dir}")
                logging.debug(f"executable_dir: {executable_dir}")

                if sys.platform == 'darwin':  # macOS系统
                    if 'XhsAi' in executable_dir:
                        # 如果在 DMG 中运行
                        browser_path = os.path.join(
                            executable_dir, "ms-playwright")
                    else:
                        # 如果已经安装到应用程序文件夹
                        browser_path = os.path.join(
                            executable_dir, "Contents", "MacOS", "ms-playwright")
                    print(f"浏览器路径: {browser_path}")
                    logging.debug(f"浏览器路径: {browser_path}")
                    chromium_path = os.path.join(
                        browser_path, "chromium-1161/chrome-mac/Chromium.app/Contents/MacOS/Chromium")
                else:
                    # Windows系统
                    browser_path = os.path.join(executable_dir, "ms-playwright")
                    print(f"浏览器路径: {browser_path}")
                    chromium_path = os.path.join(
                        browser_path, "chromium-1161", "chrome-win", "chrome.exe")

            print(f"Chromium 路径: {chromium_path}")
            logging.debug(f"Chromium 路径: {chromium_path}")
            if chromium_path:
                # 确保浏览器文件存在且有执行权限
                if os.path.exists(chromium_path):
                    os.chmod(chromium_path, 0o755)
                    launch_args['executable_path'] = chromium_path
                else:
                    raise Exception(f"浏览器文件不存在: {chromium_path}")

            # 获取默认的 Chromium 可执行文件路径
            self.browser = self.playwright.chromium.launch(**launch_args)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            print("浏览器启动成功！")
            logging.debug("浏览器启动成功！")
            # 获取当前执行文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.token_file = os.path.join(current_dir, "xiaohongshu_token.json")
            self.cookies_file = os.path.join(
                current_dir, "xiaohongshu_cookies.json")
            self.token = self._load_token()
            self._load_cookies()

        except Exception as e:
            print(f"初始化过程中出现错误: {str(e)}")
            logging.debug(f"初始化过程中出现错误: {str(e)}")
            raise

    def _load_token(self):
        """从文件加载token"""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    # 检查token是否过期
                    if token_data.get('expire_time', 0) > time.time():
                        return token_data.get('token')
            except:
                pass
        return None

    def _save_token(self, token):
        """保存token到文件"""
        token_data = {
            'token': token,
            # token有效期设为30天
            'expire_time': time.time() + 30 * 24 * 3600
        }
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f)

    def _load_cookies(self):
        """从文件加载cookies"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                    self.context.add_cookies(cookies)
            except:
                pass

    def _save_cookies(self):
        """保存cookies到文件"""
        cookies = self.context.cookies()
        with open(self.cookies_file, 'w') as f:
            json.dump(cookies, f)

    def login(self, phone, country_code="+86"):
        """登录小红书"""
        # 如果token有效则直接返回
        if self.token:
            return

        # 尝试加载cookies进行登录
        self.page.goto("https://creator.xiaohongshu.com/login")
        self._load_cookies()
        self.page.reload()
        time.sleep(3)

        # 检查是否已经登录
        if "login" not in self.page.url:
            print("使用cookies登录成功")
            self.token = self._load_token()
            self._save_cookies()
            time.sleep(2)
            return
        else:
            # 清理无效的cookies
            self.context.clear_cookies()
            print("无效的cookies，已清理")

        # 如果cookies登录失败，则进行手动登录
        self.page.goto("https://creator.xiaohongshu.com/login")
        time.sleep(1)

        # 输入手机号
        self.page.fill("//input[@placeholder='手机号']", phone)

        time.sleep(2)
        # 点击发送验证码按钮
        try:
            self.page.click(".css-uyobdj")
        except:
            try:
                self.page.click(".css-1vfl29")
            except:
                try:
                    self.page.click("//button[text()='发送验证码']")
                except:
                    print("无法找到发送验证码按钮")

        # 输入验证码
        verification_code = input("请输入验证码: ")
        self.page.fill("//input[@placeholder='验证码']", verification_code)

        # 点击登录按钮
        self.page.click(".beer-login-btn")

        # 等待登录成功
        time.sleep(3)
        # 保存cookies
        self._save_cookies()

    def post_article(self, title, content, images=None):
        """发布文章
        Args:
            title: 文章标题
            content: 文章内容
            images: 图片路径列表
        """
        time.sleep(3)
        print("点击发布按钮")
        # 点击发布按钮
        self.page.click(".btn.el-tooltip__trigger.el-tooltip__trigger")

        # 切换到上传图文
        time.sleep(3)
        tabs = self.page.query_selector_all(".creator-tab")
        if len(tabs) > 1:
            tabs[1].click()
        time.sleep(3)

        # 上传图片
        if images:
            with self.page.expect_file_chooser() as fc_info:
                self.page.click(".upload-input")
            file_chooser = fc_info.value
            file_chooser.set_files(images)
            time.sleep(1)

        time.sleep(3)
        # 输入标题
        self.page.fill(".d-text", title)

        # 输入内容
        print(content)
        self.page.fill(".ql-editor", content)

        # 发布
        time.sleep(600)
        self.page.click(".el-button.publishBtn")

    def close(self):
        """关闭浏览器"""
        self.context.close()
        self.browser.close()
        self.playwright.stop()

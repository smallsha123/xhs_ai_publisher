import os
# 静音 Qt WebEngine 初始化日志
os.environ["QT_LOGGING_RULES"] = "qt.webenginecontext.debug=false;qt.webenginecontext.info=false"
from PyQt6.QtCore import QUrl, QStandardPaths, QDateTime
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage

class SilentPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # print(f"JavaScript console message: {message}")
        # 阻止打印控制台信息
        pass



class PreviewPage(QWidget):
    def __init__(self, p=None):
        super().__init__(p)

        self.setObjectName("previewPage")
        
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        
        # 设置桌面浏览器 User-Agent
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        # 获取用户主目录
        home_dir = os.path.expanduser('~')
        cookies_dir = os.path.join(home_dir, '.xhs_system')
        profile.setPersistentStoragePath(cookies_dir)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        
        # 添加cookie变化的监听
        # profile.cookieStore().cookieAdded.connect(self.on_cookie_added)
        
        # 启用缓存以提高加载速度
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        profile.setHttpCacheMaximumSize(100 * 1024 * 1024)  # 100MB缓存
        
        # 启用所有WebEngine功能
        settings = profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.XSSAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.SpatialNavigationEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, False)
        
        # 启用媒体播放相关设置
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowGeolocationOnInsecureOrigins, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, False)
        
        # 设置默认编码
        settings.setDefaultTextEncoding("utf-8")
        
        # 注入反检测脚本
        self.web_view = QWebEngineView()
        self.web_view.setPage(SilentPage(self.web_view))  # 使用静音页面类
        
        # 加载已保存的cookie
        self.load_saved_cookies(profile)
        
        self.web_view.setUrl(QUrl("https://www.xiaohongshu.com"))
        self.web_view.setMinimumWidth(400)  # 设置最小宽度
        self.web_view.setMaximumWidth(400)  # 设置最大宽度，固定宽度
        
        # 禁用水平滚动条
        self.web_view.page().runJavaScript("""
            document.body.style.overflowX = 'hidden';
            document.documentElement.style.overflowX = 'hidden';
        """)
        
        # 页面加载完成后注入反检测脚本
        self.web_view.loadFinished.connect(self.inject_stealth_script)
        
        l.addWidget(self.web_view)
    
    def load_saved_cookies(self, profile):
        """加载已保存的cookie"""
        try:
            # 检查是否存在已保存的cookie文件
            cookie_file = os.path.join(os.path.expanduser('~'), '.xhs_system', 'comment_xiaohongshu_cookies.json')
            if os.path.exists(cookie_file):
                import json
                from PyQt6.QtCore import QDateTime
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        # 创建cookie对象
                        from PyQt6.QtNetwork import QNetworkCookie
                        qcookie = QNetworkCookie(
                            cookie['name'].encode(),
                            cookie['value'].encode()
                        )
                        if 'domain' in cookie:
                            qcookie.setDomain(cookie['domain'])
                        if 'path' in cookie:
                            qcookie.setPath(cookie['path'])
                        if 'secure' in cookie:
                            qcookie.setSecure(cookie['secure'])
                        if 'httpOnly' in cookie:
                            qcookie.setHttpOnly(cookie['httpOnly'])
                        if 'expirationDate' in cookie:
                            # 将时间戳转换为QDateTime对象
                            expiration_date = QDateTime.fromSecsSinceEpoch(cookie['expirationDate'])
                            qcookie.setExpirationDate(expiration_date)
                        
                        # 添加到cookie store
                        profile.cookieStore().setCookie(qcookie)
                print("已加载保存的cookie")
        except Exception as e:
            print(f"加载cookie时出错: {str(e)}")
    
    def inject_stealth_script(self, success):
        if success:
            try:
                # 从文件加载stealth脚本
                stealth_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "stealth.min.js")
                print(stealth_file)
                if os.path.exists(stealth_file):
                    with open(stealth_file, 'r', encoding='utf-8') as f:
                        stealth_script = f.read()
                    self.web_view.page().runJavaScript(stealth_script)
                    print("已加载stealth脚本")
                else:
                    print("stealth.js文件不存在")
            except Exception as e:
                print(f"加载stealth脚本时出错: {str(e)}")
    
    def on_cookie_added(self, cookie):
        """当有新的cookie被添加时触发"""
        try:
            cookie_data = {
                'name': cookie.name().data().decode(),
                'value': cookie.value().data().decode(),
                'domain': cookie.domain(),
                'path': cookie.path(),
                'secure': cookie.isSecure(),
                'httpOnly': cookie.isHttpOnly(),
                'expirationDate': cookie.expirationDate().toSecsSinceEpoch()
            }
            
            # 保存cookie到文件
            cookie_file = os.path.join(os.path.expanduser('~'), '.xhs_system', 'comment_xiaohongshu_cookies.json')
            import json
            try:
                if os.path.exists(cookie_file):
                    with open(cookie_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                else:
                    cookies = []
                
                # 更新或添加cookie
                found = False
                for i, existing_cookie in enumerate(cookies):
                    if existing_cookie['name'] == cookie_data['name']:
                        cookies[i] = cookie_data
                        found = True
                        break
                if not found:
                    cookies.append(cookie_data)
                
                # 保存更新后的cookies
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2)
                
                print(f"已保存cookie: {cookie_data['name']}")
            except Exception as e:
                print(f"保存cookie时出错: {str(e)}")
                
        except Exception as e:
            print(f"处理cookie时出错: {str(e)}")
  
# xhs_ai_publisher

<p align="center">
  <a href="./readme.md">简体中文</a> |
  <a href="./readme_en.md">English</a> |
</p>

## 项目简介

`xhs_ai_publisher` 是一个自动化工具，专为在小红书平台上发布文章而设计。该项目结合了图形用户界面与自动化脚本，利用大模型技术生成内容，并通过浏览器自动登录和发布文章，旨在简化内容创作与发布流程。

![软件界面效果](./images/ui.png)

## 目录介绍
```
xhs_ai_publisher/
├── src/                    #源代码目录
│   └── core/               核心功能模块
│       ├── write_xiaohongshu.py     小红书自动化操作模块
│       └── xiaohongshu_cookies.json  登录凭证存储文件
│   └── cron/               定时任务
│       ├── cron_base.py     定时
│   └── logger/              日志模块
│       ├── logger.py     日志
│   └── config/             配置
│       ├── config.py      配置文件
├── static/                 图片资源目录
├── test/                    测试目录
├── build/                  构建输出目录
├── main.py                  主程序入口
├── requirements.txt       Python依赖包列表
├── environment.yml         conda环境配置文件
├── readme.md              中文说明文档
├── readme_en.md          英文说明文档
└── .gitignore             Git忽略文件配置
```



## 功能特点

- **用户登录**：通过手机号登录小红书账户，支持自动保存和加载登录凭证。
- **内容生成**：利用大模型技术自动生成文章标题和内容。
- **图片管理**：自动下载并预览封面图和内容图片。
- **文章预览与发布**：在浏览器中预览生成的文章，并进行最终发布。

## 主要模块

### easy_ui.py

该模块使用 `tkinter` 构建图形用户界面，提供以下功能：

- **登录界面**：输入手机号进行登录。
- **内容输入**：输入自定义内容，触发内容生成。
- **内容生成**：调用后端API生成文章标题和内容，并下载相关图片。
- **图片预览**：显示生成的封面图和内容图片。
- **文章预览与发布**：在浏览器中预览并发布生成的文章。

### write_xiaohongshu.py

该模块使用 `selenium` 实现对小红书平台的自动化操作，包括：

- **登录功能**：自动完成登录流程，支持使用Cookies保存会话。
- **文章发布**：自动填写文章标题、内容，并上传图片，完成文章发布。

### xiaohongshu_img.py

该模块负责与大模型接口交互，生成文章标题和内容，并获取相关图片URL。

## 安装与使用

1. **安装依赖**

   确保已安装 `Python 3.12`，然后运行：

   ```bash
   pip install -r requirements.txt
   ```

2. **配置参数**

   修改 `write_xiaohongshu.py` 中的登录手机号和其他配置项。

3. **运行程序**

   运行用户界面：

   ```bash
   python easy_ui.py
   ```

4. **使用流程**

   - 启动程序后，输入手机号登录小红书账户。
   - 输入需要生成内容的关键词或描述，点击"生成内容"。
   - 程序将自动生成文章标题和内容，并下载相关图片。
   - 预览生成的内容和图片，确认无误后，点击"预览发布"进行发布。

## 注意事项

- 确保已安装 `Chrome` 浏览器，并下载对应版本的 `ChromeDriver`。
- 登录过程中需要输入验证码，请确保手机畅通。
- 发布文章前，请核对生成的内容和图片，以确保符合发布要求。

## 快速使用

如果您不想配置开发环境，可以直接下载打包好的Windows可执行程序：

百度网盘链接: https://pan.baidu.com/s/1rIQ-ZgyHYN_ncVXlery4yQ
提取码: iqiy

该版本为Windows独立运行版，无需安装Python环境和Chrome浏览器，开箱即用。

使用步骤:
1. 下载并解压压缩包
2. 运行文件夹中的 `easy_ui.exe`
3. 按照界面提示操作即可

注意事项:
- 仅支持Windows系统
- 首次运行可能需要等待较长时间加载
- 如遇到杀毒软件报警，请添加信任

## 联系方式
如果对项目有任何意见，欢迎加我微信交流：

### 微信
<img src="images/wechat_qr.jpg" width="200" height="200">

同时，欢迎关注我的公众号，获取更多信息：

### 公众号
<img src="images/mp_qr.jpg" width="200" height="200">

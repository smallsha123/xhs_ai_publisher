# xhs_ai_publisher

<p align="center">
  <a href="./readme.md">简体中文</a> |
  <a href="./readme_en.md">English</a> |
</p>

## Project Introduction

`xhs_ai_publisher` is an automation tool designed for publishing articles on Xiaohongshu (RED) platform. This project combines a graphical user interface with automation scripts, leveraging large language models to generate content and automating browser-based login and article publishing, aiming to streamline the content creation and publishing process.

![Software Interface](images/ui.png)

## Directory Structure
```
xhs_ai_publisher/
├── src/                    #Source code directory
│   └── core/               Core function modules
│       ├── write_xiaohongshu.py     Xiaohongshu automation module
│       └── xiaohongshu_cookies.json  Login credentials storage file
├── static/                 Image resource directory
├── test/                    Test directory
├── build/                  Build output directory
├── main.py                  Main program entry
├── requirements.txt       Python dependency list
├── environment.yml         conda environment config file
├── readme.md              Chinese documentation
├── readme_en.md          English documentation
└── .gitignore             Git ignore file configuration
```


## Key Features

- **User Login**: Login to Xiaohongshu account via phone number, with support for automatic credential saving and loading.
- **Content Generation**: Automatically generate article titles and content using large language models.
- **Image Management**: Automatically download and preview cover and content images.
- **Article Preview & Publishing**: Preview generated articles in browser and proceed with final publishing.

## Main Modules

### easy_ui.py

This module uses `tkinter` to build the graphical user interface, providing:

- **Login Interface**: Phone number input for login.
- **Content Input**: Custom content input triggering content generation.
- **Content Generation**: Call backend API to generate article titles and content, downloading related images.
- **Image Preview**: Display generated cover and content images.
- **Article Preview & Publishing**: Preview and publish generated articles in browser.

### write_xiaohongshu.py

This module uses `selenium` to implement Xiaohongshu platform automation, including:

- **Login Function**: Automate login process, supporting session preservation via Cookies.
- **Article Publishing**: Automatically fill in article titles, content, and upload images to complete publishing.

### xiaohongshu_img.py

This module handles interaction with the large language model API, generating article titles and content, and retrieving image URLs.

## Installation & Usage

1. **Install Dependencies**

   Ensure Python 3.12 is installed, then run:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Parameters**

   Modify login phone number and other configurations in `write_xiaohongshu.py`.

3. **Run Program**

   Launch the user interface:

   ```bash
   python easy_ui.py
   ```

4. **Usage Flow**

   - After startup, login to Xiaohongshu account with phone number.
   - Input keywords or descriptions for content generation, click "Generate Content".
   - Program will automatically generate article titles and content, downloading related images.
   - Preview generated content and images, click "Preview & Publish" after confirmation.

## Important Notes

- Ensure `Chrome` browser is installed with corresponding `ChromeDriver` version.
- Verification code is required during login, ensure phone is accessible.
- Review generated content and images before publishing to ensure compliance with platform requirements.

## Quick Start

If you don't want to configure the development environment, you can directly download the packaged Windows executable:

Baidu Netdisk Link: https://pan.baidu.com/s/1rIQ-ZgyHYN_ncVXlery4yQ
Extraction Code: iqiy

This version is a standalone Windows version that requires no Python environment or Chrome browser installation - it's ready to use out of the box.

Usage Steps:
1. Download and extract the compressed package
2. Run `easy_ui.exe` in the folder
3. Follow the interface prompts

Notes:
- Only supports Windows systems
- First launch may require longer loading time
- If antivirus software alerts, please add to trusted programs

## Contact Information
If you have any feedback about the project, feel free to contact me on WeChat:

### WeChat
<img src="images/wechat_qr.jpg" width="200" height="200">

Also, follow my official WeChat account for more information:

### Official Account
<img src="images/mp_qr.jpg" width="200" height="200">

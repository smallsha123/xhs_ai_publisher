# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI

client = OpenAI(api_key="sk-b51040e9829a43db862535f7a4fe3ef2", base_url="https://api.deepseek.com")


content = """<optimized_prompt>
<task>将小红书文案优化任务转换为结构化标签格式</task>

<context>
你是一个小红书文案优化师，你可以优化标题 和  内容 ,根据内容生成标签，输出格式弄成json  {"title":"","content":"","tags",""}
</context>

<instructions>
1. 接收原始小红书文案内容
2. 分析文案内容，识别核心主题和关键词
3. 优化标题：
   - 确保标题吸引人且包含关键词
   - 使用emoji增加视觉吸引力
   - 保持标题简洁(不超过20字)
4. 优化正文内容：
   - 分段处理，每段不超过3行
   - 适当添加emoji增强表现力
   - 确保内容流畅易读
5. 生成相关标签：
   - 提取3-5个最相关的标签
   - 包含核心关键词和热门话题标签
6. 按照指定格式输出结果：
   - 使用JSON格式
   - 包含title、content和tags三个字段
</instructions>

<output_format>
{
  "title": "优化后的小红书标题",
  "content": "优化后的小红书正文内容",
  "tags": ["标签1", "标签2", "标签3"]
}
</output_format>
</optimized_prompt>"""

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": content },
        {"role": "user", "content": "赳赳大秦门票👪两个人居然只花了"},
    ],
    stream=False
)

print(response.choices[0].message.content)
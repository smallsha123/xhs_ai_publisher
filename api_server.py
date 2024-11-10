from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from coze_client import CozeClient

app = FastAPI()

# 扣子大模型能力
# 初始化 Coze 客户端配置
client_id = "1155533257502"  # OAuth应用的ID
private_key_path = os.path.join(os.path.dirname(__file__), "private_key3.pem")  # 私钥文件路径
kid = "EN1pTjoQLIxtkHurKz8k2lVCvHi8IWom-e60flaXh9A"  # 公钥指纹

# 创建 Coze 客户端实例
coze_client = CozeClient(client_id, private_key_path, kid)


class ChatRequest(BaseModel):
    bot_id: str
    user_id: str 
    content: str

class WorkflowRequest(BaseModel):
    workflow_id: str
    parameters: dict

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    发送聊天请求到 Coze API
    """
    try:
        coze_client._init_coze_client()
        response = coze_client.send_coze_request(
            request.bot_id,
            request.user_id,
            request.content
        )
        if response is None:
            raise HTTPException(status_code=500, detail="请求 Coze API 失败")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow/run")
async def run_workflow(request: WorkflowRequest):
    """
    运行 Coze 工作流
    """
    try:
        coze_client._init_coze_client()
        response = coze_client.run_workflow(
            request.workflow_id,
            request.parameters
        )
        if response is None:
            raise HTTPException(status_code=500, detail="运行工作流失败")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

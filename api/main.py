import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agents.document_agent import DocumentAgent
from core.task_definition import Task
from core.llm_provider import LLMProvider
from agents.data_analyzer import DataAnalyzer
from agents.stock_analyzer import StockAnalyzer
from agents.investment_advisor import InvestmentAdvisor
from agents.market_analyzer import MarketAnalyzer, CustomJSONEncoder
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WorkflowNode(BaseModel):
    id: str
    type: str
    position: Dict[str, int]
    data: Dict[str, Any]

class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str

class Workflow(BaseModel):
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

class InvestmentRequest:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols

@app.post("/api/analyze-investment")
async def analyze_investment(request: Request) -> Dict[str, Any]:
    try:
        # 获取请求数据
        data = await request.json()
        logger.info(f"Received investment analysis request: {data}")
        
        # 验证请求数据
        if not isinstance(data, dict) or 'symbols' not in data:
            raise HTTPException(status_code=400, detail="请求格式错误：需要提供 symbols 字段")
        
        symbols = data['symbols']
        if not isinstance(symbols, list) or not symbols:
            raise HTTPException(status_code=400, detail="请求格式错误：symbols 必须是非空数组")
            
        # 创建投资顾问实例并进行分析
        advisor = InvestmentAdvisor()
        # 使用await调用异步方法
        result = await advisor.analyze_investment(symbols)
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException as e:
        logger.error(f"HTTP Exception: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error processing investment analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nodes/templates")
async def get_node_templates():
    """获取可用的节点模板"""
    return {
        "nodes": [
            {
                "type": "investmentAnalysis",
                "label": "投资分析",
                "description": "分析股票并提供投资建议",
                "category": "金融分析",
                "configFields": [
                    {
                        "name": "query",
                        "type": "text",
                        "label": "查询内容",
                        "placeholder": "输入股票代码或公司名称"
                    }
                ]
            }
        ]
    }

@app.get("/api/models")
async def get_available_models():
    llm_provider = LLMProvider()
    return {"models": llm_provider.get_available_models()}

class Task(BaseModel):
    task_type: str
    kwargs: Dict[str, Any] = {}

@app.post("/api/task")
async def handle_task(task: Task):
    try:
        logger.info(f"Received task: {task.task_type}")
        
        if task.task_type == "analyze_document":
            agent = DocumentAgent()
            result = await agent.handle_task(task)
            return JSONResponse(content={"status": "success", "data": result})
            
        elif task.task_type == "analyze_investment":
            agent = InvestmentAdvisor()
            symbols = task.kwargs.get("symbols", [])
            result = await agent.analyze_investment(symbols)
            return JSONResponse(content={"status": "success", "data": result})
            
        elif task.task_type == "analyze_market":
            agent = MarketAnalyzer()
            result = agent.handle_task(task)
            # 使用自定义JSON编码器预处理数据
            content = json.loads(json.dumps(result, cls=CustomJSONEncoder))
            return JSONResponse(content=content)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported task type: {task.task_type}")
            
    except Exception as e:
        logger.error(f"Error handling task: {str(e)}")
        error_content = json.loads(json.dumps(
            {"status": "error", "error": str(e)},
            cls=CustomJSONEncoder
        ))
        return JSONResponse(
            status_code=500,
            content=error_content
        ) 
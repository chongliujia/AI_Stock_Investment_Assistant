import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agents.document_agent import DocumentAgent
from core.task_definition import Task
from core.llm_provider import LLMProvider
from agents.data_analyzer import DataAnalyzer
from agents.stock_analyzer import StockAnalyzer
from agents.investment_advisor import InvestmentAdvisor
from agents.market_analyzer import MarketAnalyzer

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

class InvestmentRequest(BaseModel):
    query: str
    
@app.post("/api/analyze-investment")
async def analyze_investment(request: InvestmentRequest):
    try:
        logger.info(f"Received investment analysis request for: {request.query}")
        
        # 从查询中提取股票代码
        query = request.query.strip()
        
        # 如果查询中没有明确的股票代码，尝试从文本中提取
        if not any(char.isdigit() for char in query):
            # 移除常见的词语来提取股票名称
            stock_name = query.lower().replace('stock', '').replace('share', '').strip()
            # 这里可以添加股票代码查找逻辑
            symbols = stock_name
            logger.info(f"Extracted stock name: {symbols}")
        else:
            symbols = query
            logger.info(f"Using provided symbol: {symbols}")

        # 创建分析器实例
        stock_analyzer = StockAnalyzer()
        investment_advisor = InvestmentAdvisor()

        # 分析股票数据
        logger.info("Starting stock analysis...")
        analysis_task = Task(
            task_type="analyze_stocks",
            prompt="",
            kwargs={
                "analysisType": "综合分析",
                "symbols": symbols,
                "period": "1y"
            }
        )
        stock_analysis = stock_analyzer.handle_task(analysis_task)
        logger.info("Stock analysis completed")

        # 生成投资建议
        logger.info("Generating investment advice...")
        investment_task = Task(
            task_type="analyze_investment",
            prompt="",
            kwargs={
                "analysisType": "综合分析",
                "symbols": symbols,
                "riskLevel": "moderate",
                "investmentHorizon": "medium"
            }
        )
        investment_advice = investment_advisor.handle_task(investment_task)
        logger.info("Investment advice generated")

        result = {
            "status": "success",
            "data": {
                "stockAnalysis": stock_analysis,
                "investmentAdvice": {
                    "advice": investment_advice.get("advice", ""),
                    "fundamentals": investment_advice.get("fundamentals", {}),
                    "charts": investment_advice.get("charts", [])
                }
            }
        }
        logger.info("Analysis completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
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
            result = agent.handle_task(task)
            return {"status": "success", "data": result}
            
        elif task.task_type == "analyze_investment":
            agent = InvestmentAdvisor()
            result = agent.handle_task(task)
            return {"status": "success", "data": result}
            
        elif task.task_type == "analyze_market":
            agent = MarketAnalyzer()
            result = agent.handle_task(task)
            return {"status": "success", "data": result}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported task type: {task.task_type}")
            
    except Exception as e:
        logger.error(f"Error handling task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
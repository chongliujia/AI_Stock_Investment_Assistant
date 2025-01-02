from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from agents.document_agent import DocumentAgent
from core.task_definition import Task

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

@app.post("/api/workflow/execute")
async def execute_workflow(workflow: Workflow):
    try:
        # 创建文档agent
        doc_agent = DocumentAgent()
        results = []

        # 按照工作流顺序执行节点
        for node in workflow.nodes:
            if node.type == "documentGenerator":
                task = Task(
                    task_type="create_document",
                    prompt=node.data.get("prompt", ""),
                    kwargs={
                        "doc_type": node.data.get("docType", "report"),
                        "word_count": node.data.get("wordCount", 1000),
                        "lang": node.data.get("language", "en")
                    }
                )
                result = doc_agent.handle_task(task)
                results.append({
                    "nodeId": node.id,
                    "result": result
                })

        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nodes/templates")
async def get_node_templates():
    """获取可用的节点模板"""
    return {
        "nodes": [
            {
                "type": "documentGenerator",
                "label": "文档生成器",
                "description": "生成指定类型的文档",
                "category": "输出",
                "configFields": [
                    {
                        "name": "prompt",
                        "type": "textarea",
                        "label": "提示词"
                    },
                    {
                        "name": "docType",
                        "type": "select",
                        "label": "文档类型",
                        "options": ["报告", "分析", "总结"]
                    },
                    {
                        "name": "wordCount",
                        "type": "number",
                        "label": "字数"
                    },
                    {
                        "name": "language",
                        "type": "select",
                        "label": "语言",
                        "options": ["zh", "en"]
                    }
                ]
            },
            {
                "type": "researchAgent",
                "label": "研究智能体",
                "description": "收集和分析特定主题的信息",
                "category": "收集",
                "configFields": [
                    {
                        "name": "topic",
                        "type": "text",
                        "label": "研究主题"
                    },
                    {
                        "name": "depth",
                        "type": "select",
                        "label": "研究深度",
                        "options": ["基础", "深入", "专业"]
                    }
                ]
            },
            {
                "type": "dataAnalyzer",
                "label": "数据分析器",
                "description": "分析和处理数据",
                "category": "分析",
                "configFields": [
                    {
                        "name": "dataSource",
                        "type": "text",
                        "label": "数据来源"
                    },
                    {
                        "name": "analysisType",
                        "type": "select",
                        "label": "分析类型",
                        "options": ["统计分析", "趋势分析", "预测分析"]
                    }
                ]
            }
        ]
    } 
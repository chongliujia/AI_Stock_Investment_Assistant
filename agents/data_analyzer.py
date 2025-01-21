import json
from core.base_agent import BaseAgent
import numpy as np
from datetime import datetime, timedelta
from core.llm_provider import LLMProvider

class DataAnalyzer(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm_provider = LLMProvider()

    def analyze_data(self, data_type, time_range=30):
        # 模拟生成数据
        dates = [
            (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(time_range)
        ]
        dates.reverse()

        if data_type == "统计分析":
            data = {
                "type": "bar",
                "title": "数据分布统计",
                "labels": ["类别A", "类别B", "类别C", "类别D", "类别E"],
                "datasets": [{
                    "label": "数量",
                    "data": np.random.randint(50, 200, 5).tolist()
                }]
            }
        elif data_type == "趋势分析":
            data = {
                "type": "line",
                "title": "趋势分析",
                "labels": dates,
                "datasets": [{
                    "label": "指标A",
                    "data": np.random.randint(100, 200, len(dates)).tolist()
                }, {
                    "label": "指标B",
                    "data": np.random.randint(50, 150, len(dates)).tolist()
                }]
            }
        else:  # 预测分析
            data = {
                "type": "line",
                "title": "预测分析",
                "labels": dates,
                "datasets": [{
                    "label": "实际值",
                    "data": np.random.randint(100, 200, len(dates)).tolist()
                }, {
                    "label": "预测值",
                    "data": np.random.randint(90, 210, len(dates)).tolist(),
                    "borderColor": "#2196F3"
                }]
            }
        
        return data

    def handle_task(self, task):
        if task.task_type != "analyze_data":
            return f"Unsupported task type: {task.task_type}"

        analysis_type = task.kwargs.get("analysisType", "统计分析")
        result = self.analyze_data(analysis_type)
        
        return json.dumps(result) 
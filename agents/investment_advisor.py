import json
from core.base_agent import BaseAgent
from core.llm_provider import LLMProvider
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class InvestmentAdvisor(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm_provider = LLMProvider()
        self.default_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
        # 添加常见公司名称到股票代码的映射
        self.company_to_symbol = {
            'APPLE': 'AAPL',
            'TESLA': 'TSLA',
            'MICROSOFT': 'MSFT',
            'GOOGLE': 'GOOGL',
            'ALPHABET': 'GOOGL',
            'AMAZON': 'AMZN',
            'META': 'META',
            'FACEBOOK': 'META',
            'NETFLIX': 'NFLX',
            'NVIDIA': 'NVDA'
        }

    def _convert_to_symbol(self, name):
        """将公司名称转换为股票代码"""
        # 如果输入已经是股票代码格式（全大写且长度<=5），直接返回
        if name.isupper() and len(name) <= 5:
            return name
            
        # 尝试在映射表中查找（转换为大写以进行匹配）
        symbol = self.company_to_symbol.get(name.upper())
        if symbol:
            return symbol
            
        # 如果找不到对应的股票代码，返回原始输入
        return name

    def analyze_investment(self, analysis_type, symbols=None, risk_level="moderate", investment_horizon="medium"):
        try:
            # 处理输入的股票代码
            if symbols:
                if isinstance(symbols, str):
                    # 分割并转换每个输入
                    symbols = [self._convert_to_symbol(sym.strip()) for sym in symbols.split(',')]
            else:
                symbols = self.default_symbols

            logger.info(f"Analyzing stocks: {symbols}")
            
            # 获取股票数据
            stock_data = {}
            fundamentals = {}
            valid_symbols = []  # 用于跟踪成功获取数据的股票

            for symbol in symbols[:5]:  # 限制最多5个股票
                try:
                    logger.info(f"Fetching data for {symbol}")
                    stock = yf.Ticker(symbol)
                    hist = stock.history(period="1y")
                    
                    if hist.empty:
                        logger.warning(f"No historical data found for {symbol}")
                        continue
                        
                    info = stock.info
                    if not info:
                        logger.warning(f"No fundamental data found for {symbol}")
                        continue

                    # 只有当历史数据和基本面数据都获取成功时，才添加到结果中
                    stock_data[symbol] = hist
                    fundamentals[symbol] = {
                        'name': info.get('longName', symbol),
                        'sector': info.get('sector', 'Unknown'),
                        'marketCap': info.get('marketCap', 0) / 1e9,  # 转换为十亿
                        'pe': info.get('trailingPE', 0),
                        'forwardPE': info.get('forwardPE', 0),
                        'profitMargin': info.get('profitMargins', 0) * 100,
                        'dividendYield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                        'beta': info.get('beta', 0)
                    }
                    valid_symbols.append(symbol)
                    logger.info(f"Successfully fetched data for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {str(e)}")
                    continue

            if not valid_symbols:
                raise ValueError("无法获取任何有效的股票数据")

            # 生成投资建议
            try:
                advice = self._generate_investment_advice(
                    stock_data, 
                    fundamentals, 
                    risk_level, 
                    investment_horizon
                )
            except Exception as e:
                logger.error(f"Error generating investment advice: {str(e)}")
                advice = f"生成投资建议时出错: {str(e)}"

            # 生成图表数据
            try:
                charts = self._generate_analysis_charts(stock_data)
            except Exception as e:
                logger.error(f"Error generating charts: {str(e)}")
                charts = []

            return {
                "advice": advice,
                "fundamentals": fundamentals,
                "charts": charts,
                "analyzed_symbols": valid_symbols  # 添加已分析的股票列表
            }

        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return {
                "advice": f"分析过程中出错: {str(e)}",
                "fundamentals": {},
                "charts": [],
                "analyzed_symbols": []
            }

    def _generate_investment_advice(self, stock_data, fundamentals, risk_level, investment_horizon):
        # 准备提示词
        prompt = f"""作为一个投资顾问，请用简单的文字格式（不要使用markdown）为投资者提供详细的投资建议。请使用中文回答。

投资者风险偏好: {risk_level}
投资期限: {investment_horizon}

分析的股票基本面数据:
"""
        
        # 添加基本面数据到提示词
        for symbol, data in fundamentals.items():
            prompt += f"\n{symbol} ({data['name']}):"
            prompt += f"\n- 行业: {data['sector']}"
            prompt += f"\n- 市值: {data['marketCap']:.2f}B"
            prompt += f"\n- 市盈率: {data['pe']:.2f}"
            prompt += f"\n- 预期市盈率: {data['forwardPE']:.2f}"
            prompt += f"\n- 利润率: {data['profitMargin']:.2f}%"
            prompt += f"\n- 股息率: {data['dividendYield']:.2f}%"
            prompt += f"\n- Beta系数: {data['beta']:.2f}\n"

        # 添加技术分析数据
        prompt += "\n技术分析数据:"
        for symbol, data in stock_data.items():
            returns = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            volatility = data['Close'].pct_change().std() * 100
            prompt += f"\n{symbol}:"
            prompt += f"\n- 年回报率: {returns:.2f}%"
            prompt += f"\n- 波动率: {volatility:.2f}%\n"

        prompt += """
请提供以下方面的建议（使用普通文本格式，不要使用markdown或特殊格式）：

1. 总体市场评估
2. 各个股票的投资建议（买入/持有/卖出）及理由
3. 建议的投资组合配置
4. 风险提示
5. 投资时间建议

请用清晰的语言表达，避免使用任何特殊格式或标记。确保建议符合投资者的风险偏好和投资期限。"""

        # 生成建议
        messages = [
            {"role": "system", "content": "你是一个专业的投资顾问，请用清晰的普通文本格式（不使用markdown）提供投资建议。"},
            {"role": "user", "content": prompt}
        ]
        advice = self.llm_provider.generate_response(messages)
        return advice

    def _generate_analysis_charts(self, stock_data):
        charts = []
        
        try:
            # 确保所有数据使用相同的日期范围
            common_dates = None
            for data in stock_data.values():
                if common_dates is None:
                    common_dates = set(data.index)
                else:
                    common_dates &= set(data.index)
            
            common_dates = sorted(list(common_dates))
            
            # 价格走势图（标准化为相对变化）
            price_data = {
                "type": "line",
                "title": "股票价格相对变化",
                "labels": [d.strftime('%Y-%m-%d') for d in common_dates],
                "datasets": []
            }
            
            # 波动率对比图
            volatility_data = {
                "type": "bar",
                "title": "30日波动率对比",
                "labels": list(stock_data.keys()),
                "datasets": [{
                    "label": "波动率 (%)",
                    "data": [],
                    "backgroundColor": "rgba(54, 162, 235, 0.5)"
                }]
            }
            
            # 为每个股票生成数据
            for symbol, data in stock_data.items():
                # 只使用共同的日期
                filtered_data = data.loc[common_dates]
                
                # 计算相对变化（第一天为基准100）
                initial_price = filtered_data['Close'].iloc[0]
                relative_changes = (filtered_data['Close'] / initial_price) * 100
                
                price_data["datasets"].append({
                    "label": symbol,
                    "data": relative_changes.round(2).tolist(),
                    "fill": False
                })
                
                # 计算30日波动率
                volatility = filtered_data['Close'].pct_change().rolling(30).std().iloc[-1] * 100
                volatility_data["datasets"][0]["data"].append(round(volatility, 2))
            
            charts.extend([price_data, volatility_data])
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            
        return charts

    def handle_task(self, task):
        if task.task_type != "analyze_investment":
            return f"Unsupported task type: {task.task_type}"

        analysis_type = task.kwargs.get("analysisType", "综合分析")
        symbols = task.kwargs.get("symbols", None)
        risk_level = task.kwargs.get("riskLevel", "moderate")
        investment_horizon = task.kwargs.get("investmentHorizon", "medium")
        
        result = self.analyze_investment(
            analysis_type,
            symbols,
            risk_level,
            investment_horizon
        )
        
        # 确保结果可以被JSON序列化
        try:
            json.dumps(result)
            return result
        except Exception as e:
            logger.error(f"Error serializing result: {e}")
            return {
                "error": "数据序列化失败",
                "message": str(e)
            } 
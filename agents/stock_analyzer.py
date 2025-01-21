import yfinance as yf
import pandas as pd
import json
from core.base_agent import BaseAgent
from datetime import datetime, timedelta
from core.llm_provider import LLMProvider
import logging

logger = logging.getLogger(__name__)

class StockAnalyzer(BaseAgent):
    def __init__(self):
        super().__init__()
        self.default_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
        self.llm_provider = LLMProvider()

    def analyze_stocks(self, analysis_type, symbols=None, period='1mo'):
        try:
            symbols = symbols or self.default_symbols
            if isinstance(symbols, str):
                symbols = [sym.strip() for sym in symbols.split(',')]
            
            if analysis_type == "基本面分析":
                return self._analyze_fundamentals(symbols)
            elif analysis_type == "新闻分析":
                return self._analyze_news(symbols)
            
            data = {}
            for symbol in symbols[:5]:  # 限制最多5个股票
                stock = yf.Ticker(symbol)
                hist = stock.history(period=period)
                data[symbol] = hist

            if analysis_type == "价格趋势":
                return self._analyze_price_trends(data)
            elif analysis_type == "成交量分析":
                return self._analyze_volume(data)
            elif analysis_type == "技术指标":
                return self._analyze_technical_indicators(data)
            else:
                return self._analyze_price_trends(data)  # 默认分析

        except Exception as e:
            return {
                "type": "line",
                "title": f"分析出错: {str(e)}",
                "labels": [],
                "datasets": []
            }

    def _analyze_price_trends(self, data):
        labels = []
        datasets = []
        
        for symbol, df in data.items():
            if len(df) > 0:
                if not labels:
                    labels = df.index.strftime('%Y-%m-%d').tolist()
                
                datasets.append({
                    "label": symbol,
                    "data": df['Close'].round(2).tolist(),
                    "borderColor": self._get_color(len(datasets)),
                    "fill": False
                })

        return {
            "type": "line",
            "title": "股票价格趋势分析",
            "labels": labels,
            "datasets": datasets
        }

    def _analyze_volume(self, data):
        labels = []
        datasets = []
        
        for symbol, df in data.items():
            if len(df) > 0:
                if not labels:
                    labels = df.index.strftime('%Y-%m-%d').tolist()
                
                datasets.append({
                    "label": f"{symbol} 成交量",
                    "data": (df['Volume'] / 1_000_000).round(2).tolist(),  # 转换为百万股
                    "backgroundColor": self._get_color(len(datasets), 0.5),
                    "type": "bar"
                })

        return {
            "type": "bar",
            "title": "股票成交量分析（百万股）",
            "labels": labels,
            "datasets": datasets
        }

    def _analyze_technical_indicators(self, data):
        labels = []
        datasets = []
        
        for symbol, df in data.items():
            if len(df) > 0:
                if not labels:
                    labels = df.index.strftime('%Y-%m-%d').tolist()
                
                # 计算5日和20日移动平均线
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['MA20'] = df['Close'].rolling(window=20).mean()
                
                datasets.extend([
                    {
                        "label": f"{symbol} 收盘价",
                        "data": df['Close'].round(2).tolist(),
                        "borderColor": self._get_color(len(datasets)),
                        "fill": False
                    },
                    {
                        "label": f"{symbol} 5日均线",
                        "data": df['MA5'].round(2).tolist(),
                        "borderColor": self._get_color(len(datasets) + 1),
                        "borderDash": [5, 5]
                    },
                    {
                        "label": f"{symbol} 20日均线",
                        "data": df['MA20'].round(2).tolist(),
                        "borderColor": self._get_color(len(datasets) + 2),
                        "borderDash": [2, 2]
                    }
                ])

        return {
            "type": "line",
            "title": "技术指标分析",
            "labels": labels,
            "datasets": datasets
        }

    def _analyze_fundamentals(self, symbols):
        """分析股票基本面数据"""
        datasets = []
        metrics = []
        
        for symbol in symbols[:5]:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # 获取关键财务指标
                pe_ratio = info.get('trailingPE', 0)
                market_cap = info.get('marketCap', 0) / 1e9  # 转换为十亿
                revenue = info.get('totalRevenue', 0) / 1e9
                profit_margin = info.get('profitMargins', 0) * 100
                
                metrics.append({
                    'symbol': symbol,
                    'pe': round(pe_ratio, 2),
                    'marketCap': round(market_cap, 2),
                    'revenue': round(revenue, 2),
                    'profitMargin': round(profit_margin, 2)
                })
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                continue

        # 创建市值对比图表
        market_cap_data = {
            "type": "bar",
            "title": "市值对比（十亿美元）",
            "labels": [m['symbol'] for m in metrics],
            "datasets": [{
                "label": "市值",
                "data": [m['marketCap'] for m in metrics],
                "backgroundColor": self._get_color(0, 0.5)
            }]
        }
        
        # 创建PE比率对比图表
        pe_data = {
            "type": "bar",
            "title": "市盈率(P/E)对比",
            "labels": [m['symbol'] for m in metrics],
            "datasets": [{
                "label": "P/E比率",
                "data": [m['pe'] for m in metrics],
                "backgroundColor": self._get_color(1, 0.5)
            }]
        }
        
        # 创建利润率对比图表
        margin_data = {
            "type": "bar",
            "title": "利润率对比(%)",
            "labels": [m['symbol'] for m in metrics],
            "datasets": [{
                "label": "利润率",
                "data": [m['profitMargin'] for m in metrics],
                "backgroundColor": self._get_color(2, 0.5)
            }]
        }

        return {
            "type": "fundamental",
            "charts": [market_cap_data, pe_data, margin_data],
            "metrics": metrics
        }

    def _analyze_news(self, symbols):
        """分析股票相关新闻"""
        news_data = []
        sentiment_summary = []
        
        for symbol in symbols[:3]:  # 限制分析前3个股票
            try:
                stock = yf.Ticker(symbol)
                news = stock.news[:5]  # 获取最新的5条新闻
                
                # 收集新闻数据
                symbol_news = []
                for item in news:
                    news_item = {
                        'title': item.get('title', ''),
                        'publisher': item.get('publisher', ''),
                        'link': item.get('link', ''),
                        'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M')
                    }
                    symbol_news.append(news_item)
                
                # 使用LLM分析新闻情绪
                news_texts = "\n".join([f"标题: {n['title']}" for n in symbol_news])
                prompt = f"分析以下{symbol}股票的新闻标题，总结整体市场情绪（积极/中性/消极）并给出简要理由：\n{news_texts}"
                sentiment_analysis = self.llm_provider.generate_response(prompt)
                
                news_data.append({
                    'symbol': symbol,
                    'news': symbol_news
                })
                
                sentiment_summary.append({
                    'symbol': symbol,
                    'analysis': sentiment_analysis
                })
                
            except Exception as e:
                print(f"Error fetching news for {symbol}: {e}")
                continue

        return {
            "type": "news",
            "newsData": news_data,
            "sentimentAnalysis": sentiment_summary
        }

    def _get_color(self, index, alpha=1.0):
        colors = [
            f'rgba(75, 192, 192, {alpha})',
            f'rgba(255, 99, 132, {alpha})',
            f'rgba(54, 162, 235, {alpha})',
            f'rgba(255, 206, 86, {alpha})',
            f'rgba(153, 102, 255, {alpha})',
        ]
        return colors[index % len(colors)]

    def handle_task(self, task):
        if task.task_type != "analyze_stocks":
            return f"Unsupported task type: {task.task_type}"

        analysis_type = task.kwargs.get("analysisType", "价格趋势")
        symbols = task.kwargs.get("symbols", None)
        period = task.kwargs.get("period", "1mo")
        
        result = self.analyze_stocks(analysis_type, symbols, period)
        
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
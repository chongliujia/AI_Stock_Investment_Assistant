import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from core.base_agent import BaseAgent
from core.llm_provider import LLMProvider
import requests
from bs4 import BeautifulSoup
import json
import os
import ta  # 技术分析库
from pandas_datareader import data as pdr
import finnhub
from stockstats import StockDataFrame
from concurrent.futures import ThreadPoolExecutor
import time  # 添加time模块用于重试延迟

logger = logging.getLogger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (float, np.float64, np.float32)):
            if np.isnan(obj) or np.isinf(obj):
                return 0.0
            return float(obj)
        return super().default(obj)

class MarketAnalyzer(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm_provider = LLMProvider(model="gpt-4o-2024-08-06")  # 指定使用 GPT-4 模型
        self.finnhub_client = None
        self._init_api_clients()
        
    def _init_api_clients(self):
        """初始化各种API客户端"""
        # Finnhub API客户端
        finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        if finnhub_api_key:
            self.finnhub_client = finnhub.Client(api_key=finnhub_api_key)
            
    def analyze_market(self):
        """分析整体市场状况和发掘潜力股"""
        try:
            logger.info("Starting market analysis...")
            
            # 初始化结果字典
            result = {
                "market_overview": {},
                "hot_sectors": {},
                "macro_indicators": {},
                "news_summary": "",
                "potential_stocks": [],
                "market_sentiment": {},
                "analysis_report": "",
                "progress_updates": []  # 添加进度更新列表
            }

            # 1. 获取市场指数数据
            logger.info("Analyzing market indices...")
            result["market_overview"] = self._analyze_market_indices() or {}
            result["progress_updates"].append({
                "stage": "market_indices",
                "message": "已完成市场指数分析",
                "data": result["market_overview"]
            })

            # 2. 获取市场热点板块
            logger.info("Analyzing sector performance...")
            result["hot_sectors"] = self._analyze_sector_performance() or {}
            result["progress_updates"].append({
                "stage": "sector_performance",
                "message": "已完成板块分析",
                "data": result["hot_sectors"]
            })

            # 3. 获取宏观经济指标
            logger.info("Analyzing macro indicators...")
            result["macro_indicators"] = self._analyze_macro_indicators() or {}
            result["progress_updates"].append({
                "stage": "macro_indicators",
                "message": "已完成宏观指标分析",
                "data": result["macro_indicators"]
            })

            # 4. 获取最新金融新闻
            logger.info("Fetching financial news...")
            result["news_summary"] = self._fetch_financial_news() or "暂无最新市场新闻"
            result["progress_updates"].append({
                "stage": "financial_news",
                "message": "已完成新闻分析",
                "data": result["news_summary"]
            })

            # 5. 筛选潜力股
            logger.info("Screening potential stocks...")
            result["potential_stocks"] = self._screen_potential_stocks() or []
            result["progress_updates"].append({
                "stage": "potential_stocks",
                "message": "已完成潜力股筛选",
                "data": result["potential_stocks"]
            })
            
            # 6. 获取市场情绪指标
            logger.info("Analyzing market sentiment...")
            result["market_sentiment"] = self._analyze_market_sentiment() or {}
            result["progress_updates"].append({
                "stage": "market_sentiment",
                "message": "已完成市场情绪分析",
                "data": result["market_sentiment"]
            })

            # 7. 生成市场分析报告
            logger.info("Generating market report...")
            prompt = self._generate_market_report_prompt(
                result["market_overview"],
                result["hot_sectors"],
                result["macro_indicators"],
                result["news_summary"],
                result["potential_stocks"],
                result["market_sentiment"]
            )
            
            # 使用同步方式调用LLM
            result["analysis_report"] = self.llm_provider.generate_response_sync(prompt) or "暂无市场分析报告"
            result["progress_updates"].append({
                "stage": "final_report",
                "message": "已完成市场分析报告",
                "data": result["analysis_report"]
            })

            logger.info("Market analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"Market analysis error: {str(e)}", exc_info=True)
            return {
                "market_overview": {},
                "hot_sectors": {},
                "macro_indicators": {},
                "news_summary": "市场分析过程中出错",
                "potential_stocks": [],
                "market_sentiment": {},
                "analysis_report": f"市场分析过程中出错: {str(e)}",
                "progress_updates": []
            }

    def _sanitize_data(self, data):
        """递归清理数据中的特殊浮点数值"""
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, (float, np.float64, np.float32)):
            if np.isnan(data) or np.isinf(data):
                return 0.0
            return float(data)
        return data

    def _analyze_market_indices(self):
        """分析主要市场指数"""
        indices = {
            'SPY': 'S&P 500 ETF',  # 使用SPY ETF替代^GSPC
            'DIA': '道琼斯工业平均指数ETF',  # 使用DIA ETF替代^DJI
            'QQQ': '纳斯达克100ETF',  # 使用QQQ ETF替代^IXIC
            'UVXY': 'VIX波动率ETF',  # 使用UVXY ETF替代^VIX
            'TLT': '20年期国债ETF',  # 使用TLT ETF替代^TNX
            'GLD': '黄金ETF',  # 使用GLD ETF替代GC=F
            'USO': '原油ETF',  # 使用USO ETF替代CL=F
            'FXE': '欧元ETF'  # 使用FXE ETF替代EURUSD=X
        }
        
        market_data = {}
        for symbol, name in indices.items():
            for attempt in range(3):  # 最多重试3次
                try:
                    logger.info(f"Fetching data for {name} ({symbol}), attempt {attempt + 1}")
                    index = yf.Ticker(symbol)
                    hist = index.history(period="6mo", timeout=10)  # 设置较短的超时时间
                    
                    if not hist.empty:
                        # 基础指标
                        last_close = self._sanitize_data(hist['Close'].iloc[-1])
                        prev_close = self._sanitize_data(hist['Close'].iloc[-2])
                        month_ago = self._sanitize_data(hist['Close'].iloc[-22] if len(hist) >= 22 else hist['Close'].iloc[0])
                        
                        # 技术指标
                        sma_20 = self._sanitize_data(ta.trend.sma_indicator(hist['Close'], window=20).iloc[-1])
                        sma_50 = self._sanitize_data(ta.trend.sma_indicator(hist['Close'], window=50).iloc[-1])
                        rsi = self._sanitize_data(ta.momentum.rsi(hist['Close'], window=14).iloc[-1])
                        macd = self._sanitize_data(ta.trend.macd_diff(hist['Close']).iloc[-1])
                        
                        # 计算变化率时防止除以0
                        daily_change = self._sanitize_data(((last_close / prev_close) - 1) * 100 if prev_close != 0 else 0)
                        monthly_change = self._sanitize_data(((last_close / month_ago) - 1) * 100 if month_ago != 0 else 0)
                        sma20_diff = self._sanitize_data(((last_close / sma_20) - 1) * 100 if sma_20 != 0 else 0)
                        sma50_diff = self._sanitize_data(((last_close / sma_50) - 1) * 100 if sma_50 != 0 else 0)
                        
                        market_data[name] = {
                            'current': round(last_close, 2),
                            'daily_change': round(daily_change, 2),
                            'monthly_change': round(monthly_change, 2),
                            'volatility': round(self._sanitize_data(hist['Close'].pct_change().std() * 100), 2),
                            'sma20_diff': round(sma20_diff, 2),
                            'sma50_diff': round(sma50_diff, 2),
                            'rsi': round(rsi, 2),
                            'macd': round(macd, 4)
                        }
                        logger.info(f"Successfully analyzed {name}")
                        break  # 成功获取数据后跳出重试循环
                        
                    else:
                        logger.warning(f"No data available for {name} ({symbol})")
                        
                except Exception as e:
                    logger.error(f"Error analyzing index {symbol} (attempt {attempt + 1}): {str(e)}")
                    if attempt == 2:  # 最后一次尝试失败
                        continue
                    time.sleep(2 ** attempt)  # 指数退避
                    
        return market_data

    def _analyze_macro_indicators(self):
        """分析宏观经济指标"""
        try:
            # 使用FRED API获取宏观经济数据
            fred_api_key = os.getenv('FRED_API_KEY')
            if not fred_api_key:
                return {}
                
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # 获取主要经济指标
            indicators = {
                'GDP': 'GDP',
                'UNRATE': '失业率',
                'CPIAUCSL': 'CPI通胀率',
                'FEDFUNDS': '联邦基金利率',
                'M2': 'M2货币供应量',
                'INDPRO': '工业生产指数'
            }
            
            macro_data = {}
            for symbol, name in indicators.items():
                try:
                    df = pdr.DataReader(symbol, 'fred', start_date, end_date)
                    if not df.empty:
                        latest_value = df.iloc[-1].values[0]
                        prev_value = df.iloc[-2].values[0] if len(df) > 1 else None
                        
                        macro_data[name] = {
                            'value': round(latest_value, 2),
                            'change': round((latest_value - prev_value), 2) if prev_value else None,
                            'trend': 'up' if latest_value > prev_value else 'down' if prev_value else 'neutral'
                        }
                except Exception as e:
                    logger.error(f"Error fetching macro indicator {symbol}: {str(e)}")
                    continue
                    
            return macro_data
            
        except Exception as e:
            logger.error(f"Macro analysis error: {str(e)}")
            return {}

    def _analyze_market_sentiment(self):
        """分析市场情绪"""
        try:
            # 分析技术面情绪
            spy = yf.Ticker('SPY')
            hist = spy.history(period='1mo')
            
            if not hist.empty:
                # 计算RSI
                rsi = ta.momentum.rsi(hist['Close'], window=14).iloc[-1]
                
                # 计算MACD
                macd = ta.trend.macd_diff(hist['Close'])
                macd_signal = 'bullish' if macd.iloc[-1] > 0 else 'bearish'
                
                # 计算趋势
                sma_20 = ta.trend.sma_indicator(hist['Close'], window=20).iloc[-1]
                sma_50 = ta.trend.sma_indicator(hist['Close'], window=50).iloc[-1]
                current_price = hist['Close'].iloc[-1]
                
                if current_price > sma_20 and sma_20 > sma_50:
                    trend = 'bullish'
                elif current_price < sma_20 and sma_20 < sma_50:
                    trend = 'bearish'
                else:
                    trend = 'neutral'
                
                # 计算成交量趋势
                avg_volume = hist['Volume'].rolling(window=20).mean()
                volume_trend = 'up' if hist['Volume'].iloc[-1] > avg_volume.iloc[-1] else 'down'
                
                # 计算波动率
                volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
                
                # 计算技术面综合得分 (0-100)
                technical_score = 0
                if rsi < 30:  # 超卖
                    technical_score += 30
                elif rsi > 70:  # 超买
                    technical_score += 10
                else:
                    technical_score += 20
                    
                if macd_signal == 'bullish':
                    technical_score += 20
                    
                if trend == 'bullish':
                    technical_score += 30
                elif trend == 'neutral':
                    technical_score += 15
                    
                if volume_trend == 'up':
                    technical_score += 20
                
                technical_sentiment = {
                    'rsi': round(rsi, 2),
                    'macd': macd_signal,
                    'trend': trend,
                    'volume_trend': volume_trend,
                    'volatility': round(volatility, 2),
                    'score': technical_score
                }
            else:
                technical_sentiment = {
                    'rsi': 50,
                    'macd': 'neutral',
                    'trend': 'neutral',
                    'volume_trend': 'neutral',
                    'volatility': 0,
                    'score': 50
                }
            
            # 获取新闻情绪
            news_sentiment = self._analyze_news_sentiment()
            
            return {
                'technical': technical_sentiment,
                'news': news_sentiment,
                'overall_score': round((technical_sentiment['score'] + news_sentiment.get('score', 50) * 100) / 2, 2)
            }
            
        except Exception as e:
            logger.error(f"Market sentiment analysis error: {str(e)}")
            return {
                'technical': {
                    'rsi': 50,
                    'macd': 'neutral',
                    'trend': 'neutral',
                    'volume_trend': 'neutral',
                    'volatility': 0,
                    'score': 50
                },
                'news': {
                    'overall': 'neutral',
                    'score': 0.5
                },
                'overall_score': 50
            }

    def _analyze_sector_performance(self):
        """分析行业板块表现"""
        sectors = {
            'XLK': '科技板块',
            'XLF': '金融板块',
            'XLV': '医疗保健板块',
            'XLE': '能源板块',
            'XLI': '工业板块',
            'XLC': '通信服务板块',
            'XLY': '非必需消费品板块',
            'XLB': '材料板块',
            'XLRE': '房地产板块',
            'XLP': '必需消费品板块',
            'XLU': '公用事业板块'
        }
        
        sector_data = {}
        for symbol, name in sectors.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")  # 获取5天的数据以计算更准确的变化
                
                if not hist.empty:
                    # 计算涨跌幅（使用收盘价）
                    last_close = self._sanitize_data(hist['Close'].iloc[-1])
                    prev_close = self._sanitize_data(hist['Close'].iloc[-2])
                    price_change = ((last_close / prev_close - 1) * 100) if prev_close != 0 else 0
                    
                    # 计算成交量变化
                    last_volume = self._sanitize_data(hist['Volume'].iloc[-1])
                    avg_volume = self._sanitize_data(hist['Volume'].iloc[:-1].mean())
                    volume_change = ((last_volume / avg_volume - 1) * 100) if avg_volume != 0 else 0
                    
                    # 计算动量（5日变化）
                    five_day_start = self._sanitize_data(hist['Close'].iloc[0])
                    momentum = ((last_close / five_day_start - 1) * 100) if five_day_start != 0 else 0
                    
                    # 计算相对强弱（RSI）
                    rsi = self._sanitize_data(ta.momentum.rsi(hist['Close'], window=14).iloc[-1])
                    
                    # 计算MACD
                    macd = ta.trend.macd_diff(hist['Close'])
                    macd_signal = 'bullish' if macd.iloc[-1] > 0 else 'bearish'
                    
                    # 计算趋势强度
                    sma_20 = ta.trend.sma_indicator(hist['Close'], window=20).iloc[-1]
                    trend_strength = ((last_close / sma_20 - 1) * 100) if sma_20 != 0 else 0
                    
                    sector_data[name] = {
                        'symbol': symbol,
                        'price_change': round(price_change, 2),
                        'volume_change': round(volume_change, 2),
                        'momentum': round(momentum, 2),
                        'rsi': round(rsi, 2),
                        'current_price': round(last_close, 2),
                        'macd_signal': macd_signal,
                        'trend_strength': round(trend_strength, 2),
                        'trend': 'up' if price_change > 0 else 'down' if price_change < 0 else 'neutral',
                        'volume_trend': 'up' if volume_change > 0 else 'down'
                    }
                    
            except Exception as e:
                logger.error(f"Error analyzing sector {symbol}: {str(e)}")
                continue
                
        # 按涨跌幅排序
        sorted_sectors = dict(sorted(
            sector_data.items(),
            key=lambda x: x[1]['price_change'],
            reverse=True
        ))
        
        return sorted_sectors

    def _analyze_news_sentiment(self):
        """分析新闻情绪"""
        try:
            # 使用 Alpha Vantage API 获取新闻情绪数据
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            if not api_key:
                return {
                    'overall': 'neutral',
                    'score': 0
                }
                
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={api_key}&tickers=SPY,QQQ,DIA&topics=financial_markets"
            response = requests.get(url)
            
            if response.status_code != 200:
                return {
                    'overall': 'neutral',
                    'score': 0
                }
                
            data = response.json()
            feed = data.get('feed', [])
            
            if not feed:
                return {
                    'overall': 'neutral',
                    'score': 0
                }
                
            # 计算平均情绪分数
            sentiment_scores = []
            for article in feed[:10]:  # 只分析最新的10条新闻
                score = float(article.get('overall_sentiment_score', 0))
                sentiment_scores.append(score)
                
            avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            # 确定整体情绪
            if avg_score > 0.2:
                overall = 'bullish'
            elif avg_score < -0.2:
                overall = 'bearish'
            else:
                overall = 'neutral'
                
            return {
                'overall': overall,
                'score': round(avg_score, 2)
            }
            
        except Exception as e:
            logger.error(f"News sentiment analysis error: {str(e)}")
            return {
                'overall': 'neutral',
                'score': 0
            }

    def _fetch_financial_news(self):
        """获取最新金融新闻"""
        try:
            if not self.finnhub_client:
                return self._fetch_backup_news()
            
            # 获取市场新闻
            news = self.finnhub_client.general_news('general', min_id=0)
            if not news:
                return self._fetch_backup_news()
            
            # 处理新闻数据
            news_data = []
            for item in news[:50]:  # 只取最新的50条新闻
                news_data.append({
                    'title': item.get('headline', ''),
                    'summary': item.get('summary', ''),
                    'source': item.get('source', ''),
                    'url': item.get('url', '')
                })
            
            # 使用LLM分析新闻
            news_prompt = f"""请基于以下最新的市场新闻进行分析，生成一份简洁的总结。注意：请使用清晰的自然语言，不要使用任何特殊格式或标记。

最新新闻：
{json.dumps(news_data, ensure_ascii=False, indent=2)}

请分析以下几点：
1. 主要市场趋势
2. 整体市场情绪
3. 重要事件及影响

请直接输出分析内容，使用简单的自然语言，不要使用任何标题、序号或特殊格式。"""
            
            return self.llm_provider.generate_response_sync(prompt=news_prompt)
            
        except Exception as e:
            logger.error(f"News fetching error: {str(e)}")
            return self._fetch_backup_news()

    def _fetch_backup_news(self):
        """获取备用新闻数据"""
        try:
            # 使用 Yahoo Finance RSS feed 作为备用新闻源
            url = "https://finance.yahoo.com/news/rssindex"
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')[:10]  # 获取最新的10条新闻
                
                news_summary = []
                for item in items:
                    title = item.title.text if item.title else ''
                    description = item.description.text if item.description else ''
                    news_summary.append({
                        'title': title,
                        'summary': description,
                    })
                
                # 使用LLM分析新闻
                backup_prompt = f"""请基于以下最新的市场新闻，进行分析：

最新新闻：
{json.dumps(news_summary, ensure_ascii=False, indent=2)}

请分析：
1. 主要市场趋势
2. 整体市场情绪
3. 重要事件及影响

请用清晰的语言表达，避免使用任何特殊格式。"""
                
                return self.llm_provider.generate_response_sync(prompt=backup_prompt)
            
            else:
                return "目前无法获取最新市场新闻，建议稍后再试。"
                
        except Exception as e:
            logger.error(f"Backup news fetching error: {str(e)}")
            return "目前无法获取最新市场新闻，建议稍后再试。"

    def _generate_market_report_prompt(self, market_data, hot_sectors, macro_data, news_summary, potential_stocks, sentiment_data):
        """生成市场分析报告的提示词"""
        # 格式化板块数据
        formatted_sectors = []
        for name, data in hot_sectors.items():
            formatted_sectors.append(f"{name}:\n"
                                  f"- 涨跌幅: {data['price_change']}%\n"
                                  f"- 成交量变化: {data['volume_change']}%\n"
                                  f"- RSI: {data['rsi']}\n"
                                  f"- 动量: {data['momentum']}%\n"
                                  f"- MACD信号: {data['macd_signal']}\n"
                                  f"- 趋势强度: {data['trend_strength']}%")

        # 格式化宏观数据
        formatted_macro = []
        for indicator, data in macro_data.items():
            formatted_macro.append(f"{indicator}:\n"
                                f"- 当前值: {data['value']}\n"
                                f"- 变化: {data['change']}\n"
                                f"- 趋势: {data['trend']}")

        return f"""请基于以下市场数据生成一份详细的市场分析报告。注意：请使用清晰的自然语言，不要使用任何特殊格式或标记。

市场数据：

1. 市场指数概况：
{json.dumps(market_data, indent=2, ensure_ascii=False)}

2. 热门行业板块：
{''.join(formatted_sectors)}

3. 宏观经济指标：
{''.join(formatted_macro)}

4. 市场新闻摘要：
{news_summary}

5. 潜力股票：
{json.dumps(potential_stocks, indent=2, ensure_ascii=False)}

6. 市场情绪指标：
技术面情绪：
- RSI: {sentiment_data.get('technical', {}).get('rsi', 'N/A')}
- MACD: {sentiment_data.get('technical', {}).get('macd', 'N/A')}
- 趋势: {sentiment_data.get('technical', {}).get('trend', 'N/A')}
- 成交量趋势: {sentiment_data.get('technical', {}).get('volume_trend', 'N/A')}

新闻情绪：
- 整体情绪: {sentiment_data.get('news', {}).get('overall', 'N/A')}
- 情绪得分: {sentiment_data.get('news', {}).get('score', 'N/A')}

请从以下几个方面进行分析，使用简单的自然语言，不要使用任何标题、序号或特殊格式：

1. 市场整体趋势和关键风险
2. 行业机会和投资主题
3. 宏观经济影响
4. 投资策略建议"""

    def _screen_potential_stocks(self):
        """筛选潜力股票"""
        try:
            # 使用S&P 500成分股作为基础股票池
            sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(sp500_url)
            sp500_stocks = tables[0]['Symbol'].tolist()[:50]  # 限制为前50只股票以提高性能
            
            potential_stocks = []
            for symbol in sp500_stocks:
                for attempt in range(3):  # 最多重试3次
                    try:
                        logger.info(f"Analyzing stock {symbol} (attempt {attempt + 1})")
                        # 获取股票数据，设置较短的超时时间
                        stock = yf.Ticker(symbol)
                        hist = stock.history(period="6mo", timeout=10)
                        info = stock.info
                        
                        if hist.empty or not info:
                            logger.warning(f"No data available for {symbol}")
                            break  # 如果没有数据，直接跳过这只股票
                            
                        # 计算技术指标
                        close_prices = hist['Close']
                        rsi = ta.momentum.rsi(close_prices, window=14).iloc[-1]
                        macd = ta.trend.macd_diff(close_prices).iloc[-1]
                        sma_20 = ta.trend.sma_indicator(close_prices, window=20).iloc[-1]
                        sma_50 = ta.trend.sma_indicator(close_prices, window=50).iloc[-1]
                        
                        # 计算动量
                        momentum = ((close_prices.iloc[-1] / close_prices.iloc[-20]) - 1) * 100
                        
                        # 获取基本面数据
                        pe_ratio = info.get('forwardPE', 0)
                        profit_margin = info.get('profitMargins', 0)
                        if profit_margin:
                            profit_margin = profit_margin * 100
                        
                        # 评分系统
                        score = 0
                        
                        # RSI评分 (0-20分)
                        if 40 <= rsi <= 60:
                            score += 20
                        elif 30 <= rsi < 40 or 60 < rsi <= 70:
                            score += 15
                        elif rsi < 30:  # 超卖
                            score += 10
                        
                        # MACD评分 (0-20分)
                        if macd > 0:
                            score += 20
                        
                        # 均线评分 (0-20分)
                        if close_prices.iloc[-1] > sma_20 > sma_50:
                            score += 20
                        elif close_prices.iloc[-1] > sma_20:
                            score += 10
                        
                        # 动量评分 (0-20分)
                        if momentum > 0:
                            score += 20
                        elif momentum > -5:
                            score += 10
                        
                        # 基本面评分 (0-20分)
                        if 0 < pe_ratio < 30:
                            score += 10
                        if profit_margin > 10:
                            score += 10
                        
                        # 只添加评分大于60的股票
                        if score >= 60:
                            stock_data = {
                                'symbol': symbol,
                                'name': info.get('longName', symbol),
                                'sector': info.get('sector', 'Unknown'),
                                'momentum': round(momentum, 2),
                                'rsi': round(rsi, 2),
                                'pe_ratio': round(pe_ratio, 2) if pe_ratio else None,
                                'profit_margin': round(profit_margin, 2) if profit_margin else None,
                                'score': score,
                                'current_price': round(close_prices.iloc[-1], 2),
                                'volume': int(hist['Volume'].iloc[-1]),
                                'market_cap': info.get('marketCap', 0)
                            }
                            potential_stocks.append(stock_data)
                            
                        break  # 成功获取数据后跳出重试循环
                        
                    except Exception as e:
                        logger.error(f"Error analyzing stock {symbol} (attempt {attempt + 1}): {str(e)}")
                        if attempt == 2:  # 最后一次尝试失败
                            continue
                        time.sleep(2 ** attempt)  # 指数退避
            
            # 按评分排序
            potential_stocks.sort(key=lambda x: x['score'], reverse=True)
            return potential_stocks[:10]  # 返回评分最高的10只股票
            
        except Exception as e:
            logger.error(f"Error in stock screening: {str(e)}")
            return []

    def handle_task(self, task):
        """处理任务"""
        try:
            if task.task_type != "analyze_market":
                return {"error": f"Unsupported task type: {task.task_type}"}
                
            # 执行市场分析
            result = self.analyze_market()
            
            # 清理并序列化结果
            sanitized_result = self._sanitize_data(result)
            
            # 使用自定义编码器进行JSON序列化测试
            try:
                json.dumps(sanitized_result, cls=CustomJSONEncoder)
                return {"status": "success", "data": sanitized_result}
            except Exception as e:
                logger.error(f"Error serializing result: {e}")
                return {
                    "status": "error",
                    "error": "数据序列化失败",
                    "message": str(e)
                }
        except Exception as e:
            logger.error(f"Error in handle_task: {e}")
            return {
                "status": "error",
                "error": "任务处理失败",
                "message": str(e)
            } 
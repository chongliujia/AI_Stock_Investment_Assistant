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

logger = logging.getLogger(__name__)

class MarketAnalyzer(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm_provider = LLMProvider()
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
                "analysis_report": ""
            }

            # 1. 获取市场指数数据
            logger.info("Analyzing market indices...")
            result["market_overview"] = self._analyze_market_indices() or {}

            # 2. 获取市场热点板块
            logger.info("Analyzing sector performance...")
            result["hot_sectors"] = self._analyze_sector_performance() or {}

            # 3. 获取宏观经济指标
            logger.info("Analyzing macro indicators...")
            result["macro_indicators"] = self._analyze_macro_indicators() or {}

            # 4. 获取最新金融新闻
            logger.info("Fetching financial news...")
            result["news_summary"] = self._fetch_financial_news() or "暂无最新市场新闻"

            # 5. 筛选潜力股
            logger.info("Screening potential stocks...")
            result["potential_stocks"] = self._screen_potential_stocks() or []
            
            # 6. 获取市场情绪指标
            logger.info("Analyzing market sentiment...")
            result["market_sentiment"] = self._analyze_market_sentiment() or {}

            # 7. 生成市场分析报告
            logger.info("Generating market report...")
            result["analysis_report"] = self._generate_market_report(
                result["market_overview"],
                result["hot_sectors"],
                result["macro_indicators"],
                result["news_summary"],
                result["potential_stocks"],
                result["market_sentiment"]
            ) or "暂无市场分析报告"

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
                "analysis_report": f"市场分析过程中出错: {str(e)}"
            }

    def _analyze_market_indices(self):
        """分析主要市场指数"""
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': '道琼斯工业平均指数',
            '^IXIC': '纳斯达克综合指数',
            '^VIX': 'VIX波动率指数',
            '^TNX': '10年期国债收益率',
            'GC=F': '黄金期货',
            'CL=F': '原油期货',
            'EURUSD=X': '欧元/美元',
        }
        
        market_data = {}
        for symbol, name in indices.items():
            try:
                index = yf.Ticker(symbol)
                hist = index.history(period="6mo")
                if not hist.empty:
                    # 基础指标
                    last_close = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    month_ago = hist['Close'].iloc[-22] if len(hist) >= 22 else hist['Close'].iloc[0]
                    
                    # 技术指标
                    sma_20 = ta.trend.sma_indicator(hist['Close'], window=20).iloc[-1]
                    sma_50 = ta.trend.sma_indicator(hist['Close'], window=50).iloc[-1]
                    rsi = ta.momentum.rsi(hist['Close'], window=14).iloc[-1]
                    macd = ta.trend.macd_diff(hist['Close']).iloc[-1]
                    
                    market_data[name] = {
                        'current': round(last_close, 2),
                        'daily_change': round(((last_close / prev_close) - 1) * 100, 2),
                        'monthly_change': round(((last_close / month_ago) - 1) * 100, 2),
                        'volatility': round(hist['Close'].pct_change().std() * 100, 2),
                        'sma20_diff': round(((last_close / sma_20) - 1) * 100, 2),
                        'sma50_diff': round(((last_close / sma_50) - 1) * 100, 2),
                        'rsi': round(rsi, 2),
                        'macd': round(macd, 4)
                    }
            except Exception as e:
                logger.error(f"Error analyzing index {symbol}: {str(e)}")
                continue
                
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
        """分析市场情绪指标"""
        try:
            sentiment_data = {
                'technical': self._analyze_technical_sentiment(),
                'news': self._analyze_news_sentiment(),
                'options': self._analyze_options_sentiment(),
                'insider': self._analyze_insider_trading()
            }
            return sentiment_data
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return {}

    def _analyze_technical_sentiment(self):
        """分析技术面情绪"""
        try:
            spy = yf.Ticker("SPY")
            hist = spy.history(period="3mo")
            
            if not hist.empty:
                # 计算技术指标
                close = hist['Close']
                volume = hist['Volume']
                
                # 动量指标
                rsi = ta.momentum.RSIIndicator(close).rsi()
                macd = ta.trend.MACD(close)
                
                # 趋势指标
                sma20 = ta.trend.SMAIndicator(close, window=20).sma_indicator()
                sma50 = ta.trend.SMAIndicator(close, window=50).sma_indicator()
                
                # 波动率指标
                bbands = ta.volatility.BollingerBands(close)
                atr = ta.volatility.AverageTrueRange(hist['High'], hist['Low'], close)
                
                # 成交量指标
                volume_sma = ta.trend.SMAIndicator(volume, window=20).sma_indicator()
                
                latest_close = close.iloc[-1]
                
                return {
                    'rsi': round(rsi.iloc[-1], 2),
                    'macd_signal': 'bullish' if macd.macd_diff().iloc[-1] > 0 else 'bearish',
                    'trend': 'bullish' if latest_close > sma20.iloc[-1] > sma50.iloc[-1] else 'bearish',
                    'volatility': round(atr.average_true_range().iloc[-1], 2),
                    'volume_trend': 'up' if volume.iloc[-1] > volume_sma.iloc[-1] else 'down'
                }
        except Exception as e:
            logger.error(f"Technical sentiment analysis error: {str(e)}")
            return {}

    def _analyze_options_sentiment(self):
        """分析期权市场情绪"""
        try:
            if not self.finnhub_client:
                return {}
                
            # 获取SPY的期权数据
            options_data = self.finnhub_client.stock_option_chain('SPY')
            
            if not options_data:
                return {}
                
            calls_volume = 0
            puts_volume = 0
            
            for chain in options_data.get('data', []):
                if chain.get('type') == 'call':
                    calls_volume += chain.get('volume', 0)
                else:
                    puts_volume += chain.get('volume', 0)
                    
            put_call_ratio = puts_volume / calls_volume if calls_volume > 0 else 0
            
            return {
                'put_call_ratio': round(put_call_ratio, 2),
                'sentiment': 'bearish' if put_call_ratio > 1 else 'bullish',
                'calls_volume': calls_volume,
                'puts_volume': puts_volume
            }
            
        except Exception as e:
            logger.error(f"Options sentiment analysis error: {str(e)}")
            return {}

    def _analyze_insider_trading(self):
        """分析内部交易情况"""
        try:
            if not self.finnhub_client:
                return {}
                
            # 获取S&P 500公司的内部交易数据
            insider_sentiment = {}
            
            for symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']:  # 示例使用主要科技股
                try:
                    data = self.finnhub_client.stock_insider_sentiment(symbol, 
                        datetime.now().strftime('%Y-%m-%d'), 
                        (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
                        
                    if data and data.get('data'):
                        sentiment = data['data'][0]
                        insider_sentiment[symbol] = {
                            'mspr': round(sentiment.get('mspr', 0), 2),  # 月度价格变动率
                            'change': round(sentiment.get('change', 0), 2),  # 内部持股变动
                            'sentiment': 'positive' if sentiment.get('mspr', 0) > 0 else 'negative'
                        }
                except Exception as e:
                    logger.error(f"Error fetching insider data for {symbol}: {str(e)}")
                    continue
                    
            return insider_sentiment
            
        except Exception as e:
            logger.error(f"Insider trading analysis error: {str(e)}")
            return {}

    def _screen_potential_stocks(self):
        """筛选潜力股"""
        try:
            # 使用多个数据源获取股票池
            stock_universe = self._get_stock_universe()
            
            potential_stocks = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(self._analyze_single_stock, symbol) 
                          for symbol in stock_universe[:50]]  # 限制分析前50只股票
                
                for future in futures:
                    result = future.result()
                    if result:
                        potential_stocks.append(result)
            
            # 按评分排序
            potential_stocks.sort(key=lambda x: x['total_score'], reverse=True)
            return potential_stocks[:10]  # 返回前10只最具潜力的股票
            
        except Exception as e:
            logger.error(f"Stock screening error: {str(e)}")
            return []

    def _get_stock_universe(self):
        """获取股票池"""
        try:
            # 尝试获取S&P 500成分股
            sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
            return sp500['Symbol'].tolist()
        except Exception as e:
            logger.error(f"Error fetching stock universe: {str(e)}")
            # 返回备用股票列表
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 
                   'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD']

    def _analyze_single_stock(self, symbol):
        """分析单个股票"""
        try:
            logger.info(f"Analyzing stock {symbol}...")
            
            # 使用 yfinance 获取股票数据
            stock = yf.Ticker(symbol)
            
            # 获取历史数据
            hist = stock.history(period="6mo")
            if hist.empty:
                logger.warning(f"No historical data available for {symbol}")
                return None
                
            # 获取股票信息
            info = stock.info
            if not info:
                logger.warning(f"No stock info available for {symbol}")
                return None
                
            # 检查必需的数据列
            required_columns = ['Close', 'High', 'Low', 'Volume']
            if not all(col in hist.columns for col in required_columns):
                logger.error(f"Missing required columns for {symbol}")
                return None
                
            # 检查是否有足够的数据点
            if len(hist) < 20:  # 至少需要20个交易日的数据
                logger.warning(f"Insufficient historical data for {symbol}")
                return None
                
            # 确保数据有效
            if hist['Close'].isnull().any():
                logger.warning(f"Found null values in Close prices for {symbol}")
                return None
                
            # 计算技术指标
            try:
                # 使用 ta 库计算基本技术指标
                close_prices = hist['Close']
                technical_indicators = {
                    'rsi': float(ta.momentum.RSIIndicator(close_prices).rsi().iloc[-1]),
                    'macd': float(ta.trend.MACD(close_prices).macd_diff().iloc[-1]),
                    'sma_20': float(ta.trend.SMAIndicator(close_prices, window=20).sma_indicator().iloc[-1]),
                    'sma_50': float(ta.trend.SMAIndicator(close_prices, window=50).sma_indicator().iloc[-1]),
                    'close': float(close_prices.iloc[-1])
                }
            except Exception as e:
                logger.error(f"Error calculating technical indicators for {symbol}: {str(e)}")
                return None
            
            # 计算动量指标
            try:
                momentum_indicators = {
                    'price_momentum': float(((hist['Close'].iloc[-1] / hist['Close'].iloc[-20]) - 1) * 100),
                    'volume_momentum': float(((hist['Volume'].iloc[-5:].mean() / hist['Volume'].iloc[-20:-5].mean()) - 1) * 100)
                }
            except Exception as e:
                logger.error(f"Error calculating momentum indicators for {symbol}: {str(e)}")
                return None
            
            # 获取基本面指标
            fundamental_indicators = {
                'pe_ratio': float(info.get('forwardPE', 0) or 0),
                'pb_ratio': float(info.get('priceToBook', 0) or 0),
                'profit_margin': float(info.get('profitMargins', 0) or 0) * 100,
                'revenue_growth': float(info.get('revenueGrowth', 0) or 0) * 100,
                'debt_to_equity': float(info.get('debtToEquity', 0) or 0),
                'current_ratio': float(info.get('currentRatio', 0) or 0)
            }
            
            # 计算综合评分
            scores = {
                'technical_score': self._calculate_technical_score(technical_indicators),
                'momentum_score': self._calculate_momentum_score(momentum_indicators),
                'fundamental_score': self._calculate_fundamental_score(fundamental_indicators)
            }
            
            total_score = sum(scores.values()) / len(scores)
            
            # 只返回评分达到标准的股票
            if total_score >= 60:
                return {
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'technical_indicators': technical_indicators,
                    'momentum_indicators': momentum_indicators,
                    'fundamental_indicators': fundamental_indicators,
                    'scores': scores,
                    'total_score': round(total_score, 2)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {str(e)}", exc_info=True)
            return None

    def _calculate_technical_score(self, indicators):
        """计算技术分析得分"""
        score = 0
        
        try:
            # RSI指标评分 (0-40)
            rsi = indicators['rsi']
            if 40 <= rsi <= 60:  # 中性区间
                score += 20
            elif (30 <= rsi < 40) or (60 < rsi <= 70):  # 临界区间
                score += 15
            elif rsi < 30:  # 超卖区间
                score += 10
            
            # MACD评分 (0-30)
            macd = indicators['macd']
            if macd > 0:
                score += 15
                if macd > indicators['close'] * 0.01:  # MACD值超过收盘价的1%
                    score += 15
            
            # 均线评分 (0-30)
            current_price = indicators['close']
            sma_20 = indicators['sma_20']
            sma_50 = indicators['sma_50']
            
            # 判断均线多头排列
            if current_price > sma_20 > sma_50:
                score += 30
            elif current_price > sma_20:
                score += 15
            elif current_price > sma_50:
                score += 10
            
            return min(score, 100)  # 确保分数不超过100
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {str(e)}")
            return 0

    def _calculate_momentum_score(self, indicators):
        """计算动量得分"""
        score = 0
        
        # 价格动量评分
        price_momentum = indicators['price_momentum']
        if price_momentum > 0:
            score += 25
        elif price_momentum > -5:
            score += 15
            
        # 成交量动量评分
        volume_momentum = indicators['volume_momentum']
        if volume_momentum > 0:
            score += 25
        elif volume_momentum > -10:
            score += 15
            
        return score

    def _calculate_fundamental_score(self, indicators):
        """计算基本面得分"""
        score = 0
        
        # PE评分
        pe = indicators['pe_ratio']
        if 0 < pe < 30:
            score += 20
        elif 30 <= pe < 50:
            score += 10
            
        # 利润率评分
        profit_margin = indicators['profit_margin']
        if profit_margin > 20:
            score += 20
        elif profit_margin > 10:
            score += 10
            
        # 收入增长评分
        revenue_growth = indicators['revenue_growth']
        if revenue_growth > 20:
            score += 20
        elif revenue_growth > 10:
            score += 10
            
        return score

    def _analyze_sector_performance(self):
        """分析各个行业板块表现"""
        try:
            sectors = [
                'XLK',  # 科技
                'XLF',  # 金融
                'XLV',  # 医疗保健
                'XLE',  # 能源
                'XLI',  # 工业
                'XLC',  # 通信服务
                'XLP',  # 日常消费品
                'XLY',  # 非必需消费品
                'XLB',  # 材料
                'XLRE'  # 房地产
            ]
            
            sector_performance = {}
            for symbol in sectors:
                etf = yf.Ticker(symbol)
                hist = etf.history(period="1mo")
                if not hist.empty:
                    info = etf.info
                    sector_performance[info.get('shortName', symbol)] = {
                        'change': ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100,
                        'volume_change': ((hist['Volume'].iloc[-1] / hist['Volume'].mean()) - 1) * 100
                    }
            
            return sector_performance
            
        except Exception as e:
            logger.error(f"Sector analysis error: {str(e)}")
            return {}

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
        """获取并分析最新金融新闻"""
        try:
            # 使用 Alpha Vantage API 获取新闻
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            if not api_key:
                logger.warning("Alpha Vantage API key not found")
                # 使用备用新闻源
                return self._fetch_backup_news()
                
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={api_key}&topics=technology,earnings,ipo,financial_markets,economy_macro"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                news_list = data.get('feed', [])[:10]  # 获取最新的10条新闻
            else:
                logger.warning(f"Failed to fetch news from Alpha Vantage: {response.status_code}")
                return self._fetch_backup_news()

            # 准备新闻摘要
            news_summary = []
            for item in news_list:
                title = item.get('title', '')
                summary = item.get('summary', '')
                sentiment = item.get('overall_sentiment_score', 0)
                news_summary.append({
                    'title': title,
                    'summary': summary,
                    'sentiment': sentiment
                })

            # 使用LLM分析新闻
            news_prompt = f"""请基于以下最新的市场新闻，进行深入分析并提供见解：

最新新闻：
{json.dumps(news_summary, ensure_ascii=False, indent=2)}

请分析以下方面：
1. 主要市场趋势和热点
2. 整体市场情绪（看多/看空/中性）
3. 值得关注的重要事件及其潜在影响
4. 可能影响市场的风险因素

请用清晰的语言表达，避免使用任何特殊格式。重点关注这些新闻对投资者的实际影响。"""
            
            return self.llm_provider.generate_response(prompt=news_prompt)
            
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
                items = soup.find_all('item')[:5]  # 获取最新的5条新闻
                
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
                
                return self.llm_provider.generate_response(prompt=backup_prompt)
            
            else:
                return "目前无法获取最新市场新闻，建议稍后再试。"
                
        except Exception as e:
            logger.error(f"Backup news fetching error: {str(e)}")
            return "目前无法获取最新市场新闻，建议稍后再试。"

    def _generate_market_report(self, market_data, hot_sectors, macro_data, news_data, potential_stocks, sentiment_data):
        """生成市场分析报告"""
        try:
            # 准备报告数据
            report_prompt = f"""请基于以下数据生成一份市场分析报告，使用清晰的文字格式（不使用markdown）：

市场指数表现：
{json.dumps(market_data, ensure_ascii=False, indent=2)}

宏观经济指标：
{json.dumps(macro_data, ensure_ascii=False, indent=2)}

热门行业板块：
{json.dumps(hot_sectors, ensure_ascii=False, indent=2)}

最新市场新闻：
{news_data}

市场情绪指标：
{json.dumps(sentiment_data, ensure_ascii=False, indent=2)}

潜力股票：
{json.dumps(potential_stocks, ensure_ascii=False, indent=2)}

请分析以下方面：
1. 市场整体趋势和投资机会
2. 最具潜力的行业板块
3. 推荐关注的潜力股及理由
4. 风险提示

请用清晰的语言表达，避免使用任何特殊格式。"""

            return self.llm_provider.generate_response(prompt=report_prompt)
            
        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
            return "无法生成市场分析报告"

    def handle_task(self, task):
        if task.task_type != "analyze_market":
            return f"Unsupported task type: {task.task_type}"
            
        result = self.analyze_market()
        
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
import json
import os
from core.base_agent import BaseAgent
from core.llm_provider import LLMProvider
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
import numpy as np
from typing import Dict, Any, List, Optional
import time
from requests.exceptions import RequestException
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

class InvestmentAdvisor(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm_provider = LLMProvider()
        self.default_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META']
        self.cache_dir = Path("cache/stock_data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置requests session
        self.session = requests.Session()
        self.session.trust_env = False
        
        # 配置yfinance
        yf.set_tz_cache_location(str(self.cache_dir))
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

    def _get_cache_path(self, symbol: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{symbol}_data.pkl"

    def _load_from_cache(self, symbol: str) -> tuple:
        """从缓存加载数据"""
        cache_path = self._get_cache_path(symbol)
        if cache_path.exists():
            cache_age = time.time() - cache_path.stat().st_mtime
            # 如果缓存不超过10分钟，直接使用
            if cache_age < 600:  # 10 minutes
                try:
                    with open(cache_path, 'rb') as f:
                        data = pickle.load(f)
                        logger.info(f"Using cached data for {symbol}")
                        return data
                except Exception as e:
                    logger.warning(f"Failed to load cache for {symbol}: {str(e)}")
        return None

    def _save_to_cache(self, symbol: str, data: tuple):
        """保存数据到缓存"""
        try:
            cache_path = self._get_cache_path(symbol)
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Saved data to cache for {symbol}")
        except Exception as e:
            logger.warning(f"Failed to save cache for {symbol}: {str(e)}")

    def _fetch_stock_data(self, symbol: str, max_retries: int = 3) -> tuple:
        """获取股票数据，包含重试机制和缓存"""
        # 首先尝试从缓存加载
        cached_data = self._load_from_cache(symbol)
        if cached_data is not None:
            return cached_data

        for attempt in range(max_retries):
            try:
                # 配置urllib3不使用代理
                import urllib3
                urllib3.disable_warnings()
                http = urllib3.PoolManager(retries=urllib3.Retry(3))
                
                # 首先尝试使用Yahoo Finance API
                try:
                    # 添加延迟以避免请求限制
                    time.sleep(2)  # 在每次请求前添加2秒延迟
                    
                    # 尝试使用yfinance的备用方法
                    stock = yf.Ticker(symbol)
                    
                    # 首先获取基本信息
                    try:
                        info = stock.info
                    except Exception as e:
                        logger.warning(f"Failed to get info for {symbol}: {str(e)}")
                        info = {}
                    
                    # 然后获取历史数据
                    try:
                        hist = stock.history(period="1mo", interval="1d")
                    except Exception as e:
                        logger.warning(f"Failed to get history for {symbol}: {str(e)}")
                        # 尝试使用download方法
                        hist = yf.download(
                            symbol, 
                            period="1mo",
                            interval="1d",
                            progress=False,
                            timeout=20,
                            session=self.session
                        )
                    
                    if not hist.empty:
                        processed_info = {
                            "longName": info.get("longName", symbol),
                            "sector": info.get("sector", "Unknown"),
                            "marketCap": info.get("marketCap", 0),
                            "trailingPE": info.get("trailingPE", None),
                            "forwardPE": info.get("forwardPE", None),
                            "profitMargins": info.get("profitMargins", 0),
                            "dividendYield": info.get("dividendYield", 0),
                            "beta": info.get("beta", 1)
                        }
                        data = (hist, processed_info)
                        self._save_to_cache(symbol, data)
                        logger.info(f"Successfully fetched data from Yahoo Finance for {symbol}")
                        return data
                except Exception as e:
                    logger.warning(f"Failed to fetch data from Yahoo Finance for {symbol}: {str(e)}")
                    time.sleep(2)  # 在尝试下一个数据源之前添加延迟

                # 尝试使用Yahoo Finance API的备用端点
                try:
                    base_url = "https://query2.finance.yahoo.com/v8/finance/chart/"
                    params = {
                        "symbol": symbol,
                        "period1": int((datetime.now() - timedelta(days=30)).timestamp()),
                        "period2": int(datetime.now().timestamp()),
                        "interval": "1d"
                    }
                    
                    response = http.request('GET', base_url + symbol, fields=params, timeout=20)
                    if response.status == 200:
                        data = json.loads(response.data.decode('utf-8'))
                        if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                            result = data["chart"]["result"][0]
                            
                            # 构建历史数据
                            timestamps = pd.to_datetime(result["timestamp"], unit='s')
                            quotes = result["indicators"]["quote"][0]
                            
                            hist = pd.DataFrame({
                                "Open": quotes.get("open", []),
                                "High": quotes.get("high", []),
                                "Low": quotes.get("low", []),
                                "Close": quotes.get("close", []),
                                "Volume": quotes.get("volume", [])
                            }, index=timestamps)
                            
                            # 移除任何None值
                            hist = hist.dropna()
                            
                            if not hist.empty:
                                info = {
                                    "longName": symbol,
                                    "sector": "Unknown",
                                    "marketCap": 0,
                                    "trailingPE": None,
                                    "forwardPE": None,
                                    "profitMargins": 0,
                                    "dividendYield": 0,
                                    "beta": 1
                                }
                                data = (hist, info)
                                self._save_to_cache(symbol, data)
                                logger.info(f"Successfully fetched data from Yahoo Finance backup endpoint for {symbol}")
                                return data
                except Exception as e:
                    logger.warning(f"Failed to fetch data from Yahoo Finance backup endpoint for {symbol}: {str(e)}")
                    time.sleep(2)

                # 尝试使用Alpha Vantage API
                try:
                    url = "https://www.alphavantage.co/query"
                    params = {
                        "function": "TIME_SERIES_DAILY",
                        "symbol": symbol,
                        "outputsize": "compact",
                        "apikey": os.getenv("ALPHA_VANTAGE_API_KEY", "YOUR_API_KEY")
                    }
                    response = http.request('GET', url, fields=params, timeout=20)
                    if response.status == 200:
                        data = json.loads(response.data.decode('utf-8'))
                        if "Time Series (Daily)" in data:
                            hist_data = data["Time Series (Daily)"]
                            df = pd.DataFrame.from_dict(hist_data, orient='index')
                            df.index = pd.to_datetime(df.index)
                            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                            df = df.astype(float)
                            
                            info = {
                                "longName": symbol,
                                "sector": "Unknown",
                                "marketCap": 0,
                                "trailingPE": None,
                                "forwardPE": None,
                                "profitMargins": 0,
                                "dividendYield": 0,
                                "beta": 1
                            }
                            data = (df, info)
                            self._save_to_cache(symbol, data)
                            logger.info(f"Successfully fetched data from Alpha Vantage for {symbol}")
                            return data
                except Exception as e:
                    logger.warning(f"Failed to fetch data from Alpha Vantage for {symbol}: {str(e)}")

                # 尝试使用Finnhub API作为最后的备选
                try:
                    finnhub_url = "https://finnhub.io/api/v1"
                    headers = {
                        "X-Finnhub-Token": os.getenv("FINNHUB_API_KEY", "YOUR_FINNHUB_API_KEY")
                    }
                    
                    quote_response = http.request(
                        'GET',
                        f"{finnhub_url}/quote",
                        fields={"symbol": symbol},
                        headers=headers,
                        timeout=20
                    )
                    
                    if quote_response.status == 200:
                        quote_data = json.loads(quote_response.data.decode('utf-8'))
                        
                        current_price = quote_data.get("c", 0)
                        current_date = pd.Timestamp.now()
                        
                        hist = pd.DataFrame({
                            "Open": [current_price],
                            "High": [quote_data.get("h", current_price)],
                            "Low": [quote_data.get("l", current_price)],
                            "Close": [current_price],
                            "Volume": [quote_data.get("v", 0)]
                        }, index=[current_date])
                        
                        profile_response = http.request(
                            'GET',
                            f"{finnhub_url}/stock/profile2",
                            fields={"symbol": symbol},
                            headers=headers,
                            timeout=20
                        )
                        
                        if profile_response.status == 200:
                            profile_data = json.loads(profile_response.data.decode('utf-8'))
                            info = {
                                "longName": profile_data.get("name", symbol),
                                "sector": profile_data.get("finnhubIndustry", "Unknown"),
                                "marketCap": profile_data.get("marketCapitalization", 0),
                                "trailingPE": None,
                                "forwardPE": None,
                                "profitMargins": 0,
                                "dividendYield": 0,
                                "beta": 1
                            }
                            data = (hist, info)
                            self._save_to_cache(symbol, data)
                            logger.info(f"Successfully fetched data from Finnhub for {symbol}")
                            return data
                except Exception as e:
                    logger.warning(f"Failed to fetch data from Finnhub for {symbol}: {str(e)}")

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                continue

        raise ValueError(f"无法获取{symbol}的股票数据")

    def _sanitize_float(self, value: float) -> float:
        """处理浮点数，确保其在JSON可接受的范围内"""
        try:
            if value is None:
                return 0.0
            if np.isnan(value) or np.isinf(value):
                return 0.0
            # 确保数值在JSON可接受的范围内
            if abs(value) > 1e308:  # JSON的最大值限制
                return 0.0
            return float(value)
        except:
            return 0.0

    async def _analyze_company_info(self, symbol: str, info: Dict[str, Any]) -> Dict[str, str]:
        """使用LLM分析公司信息并生成详细介绍"""
        try:
            # 收集公司基本信息
            company_name = info.get("longName", symbol)
            description = info.get("longBusinessSummary", "")
            industry = info.get("industry", "未知行业")
            sector = info.get("sector", "未知板块")
            employees = info.get("fullTimeEmployees", "未知")
            
            try:
                prompt = f"""
                请根据以下公司信息，生成一个详细的公司介绍和主营业务分析。公司信息如下：

                公司名称：{company_name}
                公司描述：{description}
                所属行业：{industry}
                所属板块：{sector}
                员工人数：{employees}

                请按以下格式输出：
                1. 首先输出【公司介绍】，用3-4段话介绍公司的发展历史、市场地位、核心竞争力等。
                2. 然后输出【主营业务】，用要点的形式列出3-5个主要业务领域，每个业务领域需要详细说明其产品、服务和市场地位。每个要点以"•"开头。

                请用中文回答，确保内容专业、准确、易懂。
                """

                response = self.llm_provider.generate_response(prompt)
                
                # 分离公司介绍和主营业务
                sections = response.split("【主营业务】")
                company_intro = sections[0].replace("【公司介绍】", "").strip()
                
                # 提取主营业务列表
                businesses = []
                if len(sections) > 1:
                    businesses = [line.strip() for line in sections[1].split('\n') if line.strip().startswith('•')]
            except Exception as e:
                logger.error(f"Error generating company analysis for {symbol}: {str(e)}")
                return {
                    "introduction": f"{company_name}是一家{industry}公司，主要经营{sector}相关业务。",
                    "businesses": ["暂无主营业务信息"]
                }
            
            return {
                "introduction": company_intro,
                "businesses": businesses if businesses else ["暂无主营业务信息"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing company info for {symbol}: {str(e)}")
            return {
                "introduction": "暂无公司介绍",
                "businesses": ["暂无主营业务信息"]
            }

    async def _analyze_fundamentals(self, symbol: str, info: Dict[str, Any], hist: pd.DataFrame) -> Dict[str, Any]:
        """分析股票基本面数据"""
        try:
            # 确保历史数据不为空且包含必要的列
            if hist.empty or not all(col in hist.columns for col in ['Close', 'Volume']):
                logger.error(f"Missing required columns in historical data for {symbol}")
                return self._get_default_metrics()

            # 计算基础指标
            try:
                current_price = self._sanitize_float(hist["Close"].iloc[-1])
                initial_price = self._sanitize_float(hist["Close"].iloc[0])
                price_change = self._sanitize_float((current_price - initial_price) / initial_price * 100) if initial_price != 0 else 0.0
                
                avg_volume = self._sanitize_float(hist["Volume"].mean())
                current_volume = self._sanitize_float(hist["Volume"].iloc[-1])
                volume_change = self._sanitize_float((current_volume - avg_volume) / avg_volume * 100) if avg_volume != 0 else 0.0
                
                # 计算技术指标
                sma_20 = self._sanitize_float(hist["Close"].rolling(window=20).mean().iloc[-1])
                price_to_sma20 = self._sanitize_float((current_price - sma_20) / sma_20 * 100) if sma_20 != 0 else 0.0
            except Exception as e:
                logger.error(f"Error calculating basic metrics for {symbol}: {str(e)}")
                return self._get_default_metrics()
            
            # 获取财务指标（添加默认值和错误处理）
            market_cap = self._sanitize_float(info.get("marketCap", 0) / 1e9)
            pe_ratio = self._sanitize_float(info.get("trailingPE", 0))
            forward_pe = self._sanitize_float(info.get("forwardPE", 0))
            peg_ratio = self._sanitize_float(info.get("pegRatio", 0))
            price_to_book = self._sanitize_float(info.get("priceToBook", 0))
            profit_margin = self._sanitize_float(info.get("profitMargins", 0) * 100)
            operating_margin = self._sanitize_float(info.get("operatingMargins", 0) * 100)
            dividend_yield = self._sanitize_float(info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0)
            beta = self._sanitize_float(info.get("beta", 1))
            
            # 计算估值状态
            valuation_status = "适中"
            if pe_ratio > 0:
                if pe_ratio > 30:
                    valuation_status = "偏高"
                elif pe_ratio < 15:
                    valuation_status = "偏低"
            
            # 使用LLM生成基本面分析（添加错误处理）
            try:
                analysis_prompt = f"""
                请根据以下股票基本面数据，生成一个简短的分析报告，重点关注估值水平、盈利能力和投资风险：

                市盈率: {pe_ratio:.2f}
                预期市盈率: {forward_pe:.2f}
                市净率: {price_to_book:.2f}
                PEG比率: {peg_ratio:.2f}
                利润率: {profit_margin:.2f}%
                股息率: {dividend_yield:.2f}%
                Beta系数: {beta:.2f}

                请用中文回答，确保分析专业、客观，并给出具体的投资建议。
                """
                
                fundamental_analysis = self.llm_provider.generate_response(analysis_prompt)
            except Exception as e:
                logger.error(f"Error generating fundamental analysis for {symbol}: {str(e)}")
                fundamental_analysis = "暂时无法生成基本面分析报告。"
            
            return {
                "name": info.get("longName", symbol),
                "sector": info.get("sector", "Unknown"),
                "marketCap": market_cap,
                "pe": pe_ratio,
                "forwardPE": forward_pe,
                "profitMargin": profit_margin,
                "dividendYield": dividend_yield,
                "beta": beta,
                "basic_metrics": {
                    "current_price": current_price,
                    "price_change": price_change,
                    "avg_volume": avg_volume,
                    "volume_change": volume_change,
                    "price_to_sma20": price_to_sma20
                },
                "valuation_metrics": {
                    "market_cap": market_cap,
                    "pe_ratio": pe_ratio,
                    "forward_pe": forward_pe,
                    "peg_ratio": peg_ratio,
                    "price_to_book": price_to_book,
                    "valuation_status": valuation_status
                },
                "profitability_metrics": {
                    "profit_margin": profit_margin,
                    "operating_margin": operating_margin,
                    "dividend_yield": dividend_yield
                },
                "risk_metrics": {
                    "beta": beta,
                    "risk_level": "高" if beta > 1.5 else "低" if beta < 0.5 else "中等"
                },
                "analysis": fundamental_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing fundamentals for {symbol}: {str(e)}")
            return self._get_default_metrics()

    def _get_default_metrics(self) -> Dict[str, Any]:
        """返回默认的指标数据"""
        return {
            "name": "Unknown",
            "sector": "Unknown",
            "marketCap": 0.0,
            "pe": 0.0,
            "forwardPE": 0.0,
            "profitMargin": 0.0,
            "dividendYield": 0.0,
            "beta": 1.0,
            "basic_metrics": {
                "current_price": 0.0,
                "price_change": 0.0,
                "avg_volume": 0.0,
                "volume_change": 0.0,
                "price_to_sma20": 0.0
            },
            "valuation_metrics": {
                "market_cap": 0.0,
                "pe_ratio": 0.0,
                "forward_pe": 0.0,
                "peg_ratio": 0.0,
                "price_to_book": 0.0,
                "valuation_status": "未知"
            },
            "profitability_metrics": {
                "profit_margin": 0.0,
                "operating_margin": 0.0,
                "dividend_yield": 0.0
            },
            "risk_metrics": {
                "beta": 1.0,
                "risk_level": "中等"
            },
            "analysis": "暂无基本面分析数据。"
        }

    async def analyze_investment(self, symbols: List[str]) -> Dict[str, Any]:
        """
        分析投资标的并生成建议
        """
        logger.info(f"Analyzing stocks: {symbols}")
        
        try:
            # 初始化结果结构
            result = {
                "stockAnalysis": {
                    "type": "line",
                    "title": "Stock Price Analysis",
                    "labels": [],
                    "datasets": []
                },
                "investmentAdvice": {
                    "advice": "",
                    "companyInfo": {},
                    "fundamentals": {},
                    "charts": []
                }
            }
            
            for symbol in symbols:
                logger.info(f"Fetching data for {symbol}")
                try:
                    stock_data = self._fetch_stock_data(symbol)
                    if stock_data is None:
                        continue
                        
                    hist, info = stock_data  # Unpack the tuple
                    
                    # 分析基本面数据（异步操作）
                    fundamentals = await self._analyze_fundamentals(symbol, info, hist)
                    result["investmentAdvice"]["fundamentals"][symbol] = fundamentals
                    
                    # 分析公司信息（异步操作）
                    company_info = await self._analyze_company_info(symbol, info)
                    result["investmentAdvice"]["companyInfo"][symbol] = {
                        "name": info.get("longName", symbol),
                        "introduction": company_info["introduction"],
                        "industry": info.get("industry", "未知行业"),
                        "sector": info.get("sector", "未知板块"),
                        "website": info.get("website", ""),
                        "country": info.get("country", ""),
                        "employees": info.get("fullTimeEmployees", 0),
                        "mainBusinesses": company_info["businesses"]
                    }
                    
                    # 生成图表数据（同步操作）
                    charts = self._generate_charts(symbol, hist)
                    result["investmentAdvice"]["charts"].extend(charts)
                    
                    # 合并公司信息分析和投资建议生成（同步操作）
                    prompt = f"""
                    请基于以下信息生成详细的公司分析和投资建议：
                    
                    公司代码：{symbol}
                    公司简介：{company_info['introduction']}
                    主营业务：{' '.join(company_info['businesses'])}
                    基本面数据：{fundamentals}
                    
                    请提供以下格式的分析：
                    1. 财务分析（基于提供的基本面数据）
                    2. 投资建议（包括投资评级、风险提示）
                    """
                    
                    analysis = self.llm_provider.generate_response(prompt)
                    
                    # 解析LLM响应
                    sections = analysis.split("\n\n")
                    if len(sections) >= 2:
                        result["investmentAdvice"]["advice"] = "\n\n".join(sections)
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {str(e)}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_investment: {str(e)}")
            raise

    def _generate_charts(self, symbol: str, hist: pd.DataFrame) -> List[Dict[str, Any]]:
        """生成图表数据"""
        try:
            if hist.empty:
                return []
            
            price_chart = {
                "type": "line",
                "title": f"{symbol} Price History",
                "labels": hist.index.strftime('%Y-%m-%d').tolist(),
                "datasets": [{
                    "label": "Price",
                    "data": hist['Close'].tolist(),
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                }]
            }
            
            volume_chart = {
                "type": "bar",
                "title": f"{symbol} Volume History",
                "labels": hist.index.strftime('%Y-%m-%d').tolist(),
                "datasets": [{
                    "label": "Volume",
                    "data": hist['Volume'].tolist(),
                    "backgroundColor": "rgb(153, 102, 255)",
                }]
            }
            
            return [price_chart, volume_chart]
        except Exception as e:
            logger.error(f"Error generating charts for {symbol}: {str(e)}")
            return []

    async def _analyze_company_businesses(self, symbol: str, info: Dict[str, Any]) -> List[str]:
        """分析公司主营业务"""
        try:
            # 从公司描述中提取主营业务
            description = info.get("longBusinessSummary", "")
            if not description:
                return ["暂无主营业务信息"]

            # 使用LLM分析主营业务
            prompt = f"""
            请根据以下公司描述，列出该公司的3-5个主要业务领域，每个业务领域用一句话描述：

            公司描述：
            {description}

            请用中文回答，直接列出业务领域，不要有其他内容。每行以"•"开头。
            """

            response = await self.llm_provider.generate_response(prompt)
            
            # 处理响应
            businesses = [line.strip() for line in response.split('\n') if line.strip().startswith('•')]
            
            return businesses if businesses else ["暂无主营业务信息"]
            
        except Exception as e:
            logger.error(f"Error analyzing businesses for {symbol}: {str(e)}")
            return ["暂无主营业务信息"]

    def _convert_to_symbol(self, company: str) -> str:
        """将公司名称转换为股票代码"""
        company = company.lower()
        company_to_symbol = {
            'tesla': 'TSLA',
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'amazon': 'AMZN',
            'meta': 'META',
            'netflix': 'NFLX',
            'nvidia': 'NVDA',
        }
        
        # 如果输入的是股票代码格式，直接返回大写形式
        if company.isupper() and len(company) <= 5:
            return company
            
        # 尝试从映射中获取股票代码
        symbol = company_to_symbol.get(company)
        if symbol:
            return symbol
            
        # 如果找不到映射，假设输入的就是股票代码
        return company.upper()

    async def handle_task(self, task):
        if task.task_type != "analyze_investment":
            return f"Unsupported task type: {task.task_type}"

        symbols = task.kwargs.get("symbols", None)
        
        try:
            # Properly await the analyze_investment coroutine
            result = await self.analyze_investment(symbols)
            
            # Ensure result can be JSON serialized
            try:
                json.dumps(result)
                return result
            except Exception as e:
                logger.error(f"Error serializing result: {e}")
                return {
                    "error": "数据序列化失败",
                    "message": str(e)
                }
        except Exception as e:
            logger.error(f"Error in handle_task: {str(e)}")
            return {
                "error": "分析过程出错",
                "message": str(e)
            } 
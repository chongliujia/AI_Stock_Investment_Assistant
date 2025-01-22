import logging
from functools import lru_cache
from typing import Dict, List, Optional, Union, Any
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class InvestmentAdvisor:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = timedelta(minutes=5)
        self.llm_provider = LLMProvider()
    
    def _get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从缓存中获取数据"""
        if symbol in self.cache:
            data, timestamp = self.cache[symbol]
            if datetime.now() - timestamp < self.cache_timeout:
                return data
            del self.cache[symbol]
        return None

    def _cache_data(self, symbol: str, data: Dict[str, Any]) -> None:
        """缓存数据"""
        self.cache[symbol] = (data, datetime.now())

    @lru_cache(maxsize=100)
    def _convert_to_symbol(self, query: str) -> str:
        """将公司名称转换为股票代码"""
        query = query.upper()
        company_to_symbol = {
            'APPLE': 'AAPL',
            'TESLA': 'TSLA',
            'MICROSOFT': 'MSFT',
            'GOOGLE': 'GOOGL',
            'AMAZON': 'AMZN',
            'META': 'META',
            'NETFLIX': 'NFLX',
            'NVIDIA': 'NVDA',
        }
        return company_to_symbol.get(query, query)

    def _sanitize_float(self, value: Any) -> float:
        """处理浮点数，确保JSON兼容"""
        try:
            if pd.isna(value) or np.isinf(value):
                return 0.0
            value = float(value)
            if abs(value) > 1e308:  # JSON的最大值限制
                return 0.0
            return value
        except (TypeError, ValueError):
            return 0.0

    def _fetch_stock_data(self, symbol: str) -> Optional[yf.Ticker]:
        """获取股票数据"""
        try:
            stock = yf.Ticker(symbol)
            # 验证是否能获取到数据
            hist = stock.history(period="1y")
            if hist.empty:
                logger.warning(f"无法获取股票数据: {symbol}")
                return None
            return stock
        except Exception as e:
            logger.error(f"获取股票数据时出错 {symbol}: {str(e)}")
            return None

    def _generate_charts(self, symbol: str, stock: yf.Ticker) -> List[Dict[str, Any]]:
        """生成图表数据"""
        try:
            charts = []
            hist = stock.history(period="1y")
            
            if not hist.empty:
                dates = hist.index.strftime('%Y-%m-%d').tolist()
                
                # 添加股价走势图
                price_chart = {
                    "type": "line",
                    "title": "股价走势",
                    "labels": dates,
                    "datasets": [{
                        "label": symbol,
                        "data": hist['Close'].tolist(),
                    }]
                }
                
                # 添加交易量图
                volume_chart = {
                    "type": "bar",
                    "title": "交易量",
                    "labels": dates,
                    "datasets": [{
                        "label": symbol,
                        "data": hist['Volume'].tolist(),
                    }]
                }
                
                charts.append(price_chart)
                charts.append(volume_chart)
                
            return charts
            
        except Exception as e:
            logger.error(f"生成图表时出错: {str(e)}")
            return []

    def _analyze_fundamentals(self, symbol: str, stock: yf.Ticker) -> Dict[str, Any]:
        """分析股票基本面数据"""
        try:
            hist = stock.history(period="1y")
            info = stock.info
            
            if hist.empty:
                return self._get_default_metrics()
                
            current_price = self._sanitize_float(hist['Close'].iloc[-1])
            price_change = self._sanitize_float((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100)
            
            fundamentals = {
                "basic_metrics": {
                    "current_price": current_price,
                    "price_change": price_change,
                    "avg_volume": self._sanitize_float(hist['Volume'].mean()),
                    "volume_change": self._sanitize_float((hist['Volume'].iloc[-1] - hist['Volume'].mean()) / hist['Volume'].mean() * 100),
                    "price_to_sma20": self._sanitize_float(current_price / hist['Close'].rolling(window=20).mean().iloc[-1])
                },
                "valuation_metrics": {
                    "market_cap": self._sanitize_float(info.get('marketCap', 0) / 1e9),  # 转换为十亿
                    "pe_ratio": self._sanitize_float(info.get('trailingPE', 0)),
                    "forward_pe": self._sanitize_float(info.get('forwardPE', 0)),
                    "peg_ratio": self._sanitize_float(info.get('pegRatio', 0)),
                    "price_to_book": self._sanitize_float(info.get('priceToBook', 0)),
                    "valuation_status": self._get_valuation_status(info.get('trailingPE', 0))
                },
                "profitability_metrics": {
                    "profit_margin": self._sanitize_float(info.get('profitMargins', 0) * 100),
                    "operating_margin": self._sanitize_float(info.get('operatingMargins', 0) * 100),
                    "dividend_yield": self._sanitize_float(info.get('dividendYield', 0) * 100)
                },
                "risk_metrics": {
                    "beta": self._sanitize_float(info.get('beta', 0)),
                    "risk_level": self._get_risk_level(info.get('beta', 0))
                }
            }
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"分析基本面数据时出错 {symbol}: {str(e)}")
            return self._get_default_metrics()

    def _generate_investment_advice(self, symbol: str, fundamentals: Dict[str, Any]) -> str:
        """生成投资建议"""
        try:
            prompt = f"""基于以下基本面数据生成详细的投资建议：
            
            股票代码：{symbol}
            当前价格：${fundamentals['basic_metrics']['current_price']:.2f}
            价格变动：{fundamentals['basic_metrics']['price_change']:.2f}%
            市值：{fundamentals['valuation_metrics']['market_cap']:.2f}B
            市盈率：{fundamentals['valuation_metrics']['pe_ratio']:.2f}
            预期市盈率：{fundamentals['valuation_metrics']['forward_pe']:.2f}
            PEG比率：{fundamentals['valuation_metrics']['peg_ratio']:.2f}
            市净率：{fundamentals['valuation_metrics']['price_to_book']:.2f}
            利润率：{fundamentals['profitability_metrics']['profit_margin']:.2f}%
            Beta系数：{fundamentals['risk_metrics']['beta']:.2f}
            
            请从估值水平、盈利能力和投资风险三个维度进行分析，并给出具体的投资建议。
            """
            
            # 使用同步方式调用
            response = self.llm_provider.generate_response_sync(prompt)
            return response
            
        except Exception as e:
            logger.error(f"生成投资建议时出错: {str(e)}")
            return "无法生成投资建议"

    def analyze_investment(self, symbols: List[str]) -> Dict[str, Any]:
        """分析投资建议"""
        try:
            logger.info(f"Analyzing stocks: {symbols}")
            result = {
                "stockAnalysis": {
                    "type": "line",
                    "title": "股价走势",
                    "labels": [],
                    "datasets": []
                },
                "investmentAdvice": {
                    "advice": "",
                    "fundamentals": {},
                    "charts": [],
                    "companyInfo": {}
                }
            }
            
            for symbol in symbols:
                try:
                    # 转换股票代码
                    symbol = self._convert_to_symbol(symbol)
                    logger.info(f"Fetching data for {symbol}")
                    
                    # 检查缓存
                    cached_data = self._get_cached_data(symbol)
                    if cached_data:
                        logger.info(f"Using cached data for {symbol}")
                        result["investmentAdvice"]["fundamentals"][symbol] = cached_data["fundamentals"]
                        result["investmentAdvice"]["companyInfo"] = cached_data["companyInfo"]
                        continue
                    
                    # 获取股票数据
                    stock_data = self._fetch_stock_data(symbol)
                    if stock_data is None:
                        logger.warning(f"Failed to fetch data for {symbol}")
                        continue
                    
                    # 同步操作：基本面分析和图表生成
                    fundamentals = self._analyze_fundamentals(symbol, stock_data)
                    charts = self._generate_charts(symbol, stock_data)
                    
                    # 同步操作：公司信息分析和投资建议
                    company_info = self._analyze_company_info(symbol, stock_data)
                    advice = self._generate_investment_advice(symbol, fundamentals)
                    
                    # 更新结果
                    result["investmentAdvice"]["fundamentals"][symbol] = fundamentals
                    result["investmentAdvice"]["charts"] = charts
                    result["investmentAdvice"]["companyInfo"] = company_info
                    result["investmentAdvice"]["advice"] = advice
                    
                    # 缓存数据
                    self._cache_data(symbol, {
                        "fundamentals": fundamentals,
                        "companyInfo": company_info
                    })
                    
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {str(e)}")
                    continue
            
            if not result["investmentAdvice"]["fundamentals"]:
                raise ValueError("No valid stock data available for analysis")
                
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_investment: {str(e)}")
            raise

    def _analyze_company_info(self, symbol: str, stock: yf.Ticker) -> Dict[str, Any]:
        """分析公司信息"""
        try:
            info = stock.info
            prompt = f"""分析以下公司信息并生成详细的公司介绍和主要业务分析：
            公司名称：{info.get('longName', symbol)}
            行业：{info.get('industry', '未知')}
            板块：{info.get('sector', '未知')}
            简介：{info.get('longBusinessSummary', '未知')}
            """
            
            # 使用同步方式调用
            response = self.llm_provider.generate_response_sync(prompt)
            
            # 解析响应
            sections = response.split('\n\n')
            introduction = sections[0] if len(sections) > 0 else ""
            businesses = sections[1].split('\n')[1:] if len(sections) > 1 else []
            
            return {
                "name": info.get('longName', symbol),
                "introduction": introduction,
                "industry": info.get('industry', '未知'),
                "sector": info.get('sector', '未知'),
                "website": info.get('website', '未知'),
                "country": info.get('country', '未知'),
                "employees": info.get('fullTimeEmployees', 0),
                "mainBusinesses": businesses
            }
        except Exception as e:
            logger.error(f"分析公司信息时出错 {symbol}: {str(e)}")
            return {
                "name": symbol,
                "introduction": "无法获取公司介绍",
                "industry": "未知",
                "sector": "未知",
                "website": "未知",
                "country": "未知",
                "employees": 0,
                "mainBusinesses": []
            }

    def _get_valuation_status(self, pe_ratio: float) -> str:
        """评估估值状态"""
        if pe_ratio <= 0:
            return "无法评估"
        elif pe_ratio > 30:
            return "高估"
        elif pe_ratio < 15:
            return "低估"
        else:
            return "适中"

    def _get_risk_level(self, beta: float) -> str:
        """评估风险等级"""
        if beta <= 0:
            return "无法评估"
        elif beta > 1.5:
            return "高风险"
        elif beta < 0.5:
            return "低风险"
        else:
            return "中等风险"

    def _get_default_metrics(self) -> Dict[str, Any]:
        """获取默认指标"""
        return {
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
                "valuation_status": "无法评估"
            },
            "profitability_metrics": {
                "profit_margin": 0.0,
                "operating_margin": 0.0,
                "dividend_yield": 0.0
            },
            "risk_metrics": {
                "beta": 0.0,
                "risk_level": "无法评估"
            }
        } 
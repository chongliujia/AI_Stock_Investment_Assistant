import logging
from functools import lru_cache
from typing import Dict, List, Optional, Union, Any, Tuple
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.llm_provider import LLMProvider
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, ForceIndexIndicator

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
        # 统一转换为大写并移除多余空格
        query = query.upper().strip()
        
        # 常见公司名称映射
        company_to_symbol = {
            'APPLE': 'AAPL',
            'TESLA': 'TSLA',
            'MICROSOFT': 'MSFT',
            'GOOGLE': 'GOOGL',
            'ALPHABET': 'GOOGL',
            'AMAZON': 'AMZN',
            'META': 'META',
            'FACEBOOK': 'META',
            'NETFLIX': 'NFLX',
            'NVIDIA': 'NVDA',
            'AMD': 'AMD',
            'INTEL': 'INTC',
            'IBM': 'IBM',
            'COCA COLA': 'KO',
            'COCA-COLA': 'KO',
            'NIKE': 'NKE',
            'DISNEY': 'DIS',
            'WALMART': 'WMT',
            'JPMORGAN': 'JPM',
            'JP MORGAN': 'JPM',
            'GOLDMAN SACHS': 'GS',
            'BOEING': 'BA',
            'MCDONALDS': 'MCD',
            "MCDONALD'S": 'MCD',
            'VISA': 'V',
            'MASTERCARD': 'MA'
        }
        
        # 检查是否已经是有效的股票代码格式
        if len(query) <= 5 and query.isalpha():
            return query
            
        # 尝试从映射中获取股票代码
        # 1. 直接匹配
        if query in company_to_symbol:
            return company_to_symbol[query]
            
        # 2. 移除常见后缀后匹配
        common_suffixes = [' INC', ' CORP', ' CORPORATION', ' CO', ' COMPANY', ' LTD', ' LIMITED', ' GROUP', ' HOLDINGS', ' TECHNOLOGIES']
        clean_query = query
        for suffix in common_suffixes:
            if clean_query.endswith(suffix):
                clean_query = clean_query[:-len(suffix)]
                break
                
        if clean_query in company_to_symbol:
            return company_to_symbol[clean_query]
            
        # 3. 如果没有找到匹配，返回原始输入
        # 记录未匹配的公司名称以便后续扩展映射
        logger.info(f"未找到股票代码映射: {query}")
        return query

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
            # 转换公司名称为股票代码
            symbol = self._convert_to_symbol(symbol)
            logger.info(f"Fetching data for symbol: {symbol}")
            
            stock = yf.Ticker(symbol)
            # 验证是否能获取到数据
            hist = stock.history(period="1y")
            if hist.empty:
                logger.warning(f"无法获取股票数据: {symbol}")
                return None
                
            logger.info(f"Successfully fetched data for {symbol}")
            return stock
        except Exception as e:
            logger.error(f"获取股票数据时出错 {symbol}: {str(e)}")
            return None

    def _generate_charts(self, symbol: str, hist: pd.DataFrame, prediction_result: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """生成图表数据"""
        try:
            if hist.empty:
                return []
            
            # 历史价格图表
            price_data = hist['Close'].tolist()
            dates = hist.index.strftime('%Y-%m-%d').tolist()
            
            # 如果有预测数据，添加到图表中
            if prediction_result and prediction_result['predicted_prices']:
                price_data.extend(prediction_result['predicted_prices'])
                dates.extend(prediction_result['prediction_dates'])
            
            price_chart = {
                "type": "line",
                "title": f"{symbol} 价格走势与预测",
                "labels": dates,
                "datasets": [
                    {
                        "label": "历史价格",
                        "data": hist['Close'].tolist(),
                        "borderColor": "rgb(75, 192, 192)",
                        "tension": 0.1
                    }
                ]
            }
            
            # 如果有预测数据，添加预测数据集
            if prediction_result and prediction_result['predicted_prices']:
                price_chart["datasets"].append({
                    "label": "预测价格",
                    "data": [None] * len(hist) + prediction_result['predicted_prices'],
                    "borderColor": "rgb(255, 99, 132)",
                    "borderDash": [5, 5],
                    "tension": 0.1
                })
            
            # 成交量图表
            volume_chart = {
                "type": "bar",
                "title": f"{symbol} 成交量",
                "labels": hist.index.strftime('%Y-%m-%d').tolist(),
                "datasets": [{
                    "label": "成交量",
                    "data": hist['Volume'].tolist(),
                    "backgroundColor": "rgb(153, 102, 255)",
                }]
            }
            
            # 技术指标图表
            if prediction_result and prediction_result['technical_indicators']:
                indicators = prediction_result['technical_indicators']
                technical_chart = {
                    "type": "line",
                    "title": f"{symbol} 技术指标",
                    "labels": hist.index.strftime('%Y-%m-%d').tolist()[-30:],  # 只显示最近30天
                    "datasets": [
                        {
                            "label": "20日均线",
                            "data": [indicators['sma_20']] * 30,
                            "borderColor": "rgb(255, 159, 64)",
                            "tension": 0.1
                        },
                        {
                            "label": "50日均线",
                            "data": [indicators['sma_50']] * 30,
                            "borderColor": "rgb(54, 162, 235)",
                            "tension": 0.1
                        },
                        {
                            "label": "布林带上轨",
                            "data": [indicators['bb_upper']] * 30,
                            "borderColor": "rgb(75, 192, 192)",
                            "borderDash": [5, 5],
                            "tension": 0.1
                        },
                        {
                            "label": "布林带下轨",
                            "data": [indicators['bb_lower']] * 30,
                            "borderColor": "rgb(75, 192, 192)",
                            "borderDash": [5, 5],
                            "tension": 0.1
                        }
                    ]
                }
                return [price_chart, volume_chart, technical_chart]
            
            return [price_chart, volume_chart]
            
        except Exception as e:
            logger.error(f"Error generating charts for {symbol}: {str(e)}")
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

    async def _analyze_stock_with_gpt4(self, symbol: str, hist: pd.DataFrame, fundamentals: Dict[str, Any], market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """使用GPT-4-Turbo-Preview进行深度分析"""
        try:
            # 准备历史数据分析
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # 年化波动率
            annual_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * (252 / len(hist))
            sharpe_ratio = (annual_return - 0.02) / volatility if volatility != 0 else 0  # 假设无风险利率为2%
            
            # 计算动量指标
            momentum_20d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100 if len(hist) >= 20 else 0
            momentum_60d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-60] - 1) * 100 if len(hist) >= 60 else 0
            
            # 计算支撑和阻力位
            price_range = hist['Close'].max() - hist['Close'].min()
            support_levels = [
                hist['Close'].min() + price_range * level 
                for level in [0.236, 0.382, 0.5]  # 斐波那契水平
            ]
            resistance_levels = [
                hist['Close'].max() - price_range * level 
                for level in [0.236, 0.382, 0.5]  # 斐波那契水平
            ]
            
            # 计算波动性指标
            atr = AverageTrueRange(high=hist['High'], low=hist['Low'], close=hist['Close'])
            current_atr = atr.average_true_range().iloc[-1]
            atr_percent = (current_atr / hist['Close'].iloc[-1]) * 100
            
            # 计算成交量分析
            avg_volume = hist['Volume'].mean()
            recent_volume = hist['Volume'].iloc[-5:].mean()
            volume_trend = "上升" if recent_volume > avg_volume * 1.2 else "下降" if recent_volume < avg_volume * 0.8 else "平稳"
            
            prompt = f"""
            作为一位专业的量化分析师和投资顾问，请基于以下详细数据对{symbol}股票进行深度分析：

            1. 量化指标分析：
            - 年化收益率: {annual_return:.2%}
            - 年化波动率: {volatility:.2%}
            - 夏普比率: {sharpe_ratio:.2f}
            - 20日动量: {momentum_20d:.2f}%
            - 60日动量: {momentum_60d:.2f}%
            - ATR占比: {atr_percent:.2f}%

            2. 技术水平：
            支撑位：
            - 强支撑: ${support_levels[0]:.2f}
            - 中支撑: ${support_levels[1]:.2f}
            - 弱支撑: ${support_levels[2]:.2f}
            
            阻力位：
            - 强阻力: ${resistance_levels[0]:.2f}
            - 中阻力: ${resistance_levels[1]:.2f}
            - 弱阻力: ${resistance_levels[2]:.2f}

            3. 成交量分析：
            - 平均成交量: {avg_volume:,.0f}
            - 近期成交量: {recent_volume:,.0f}
            - 成交量趋势: {volume_trend}

            4. 基本面数据：
            - 当前价格: ${fundamentals['basic_metrics']['current_price']}
            - 市值: ${fundamentals['valuation_metrics']['market_cap']}B
            - 市盈率: {fundamentals['valuation_metrics']['pe_ratio']}
            - 市净率: {fundamentals['valuation_metrics']['price_to_book']}
            - 利润率: {fundamentals['profitability_metrics']['profit_margin']}%
            - Beta系数: {fundamentals['risk_metrics']['beta']}

            5. 市场环境：
            - 市场趋势: {market_analysis['market_trend']}
            - 波动性: {market_analysis['volatility']}
            - 市场强度: {market_analysis['strength']}
            - 风险水平: {market_analysis['risk_level']}

            请提供以下深度分析：

            1. 量化分析：
            - 详细评估风险收益特征
            - 基于夏普比率和波动率的风险调整后收益分析
            - 动量趋势分析

            2. 技术分析：
            - 重要支撑位和阻力位的突破可能性
            - 基于成交量的价格趋势可信度
            - 短期和中期的技术形态

            3. 估值分析：
            - 相对估值水平评估
            - 基于行业对标的估值溢价/折价分析
            - 潜在的估值修复空间

            4. 风险评估：
            - 系统性风险暴露（基于Beta）
            - 个股特有风险因素
            - 市场环境对该股票的潜在影响

            5. 交易建议：
            - 建议持仓时间（短期/中期/长期）
            - 分批建仓/减仓价位
            - 具体的止损止盈策略
            - 仓位管理建议
            - 对冲策略建议（如需要）

            请用专业但易懂的语言回答，注重实用性和可操作性。对于每个关键结论，请提供具体的数据支持。
            """
            
            # 使用GPT-4-Turbo-Preview生成分析
            analysis = await self.llm_provider.generate_response(prompt, model="gpt-4-turbo-preview")
            
            return {
                "quantitative_metrics": {
                    "annual_return": annual_return,
                    "volatility": volatility,
                    "sharpe_ratio": sharpe_ratio,
                    "momentum_20d": momentum_20d,
                    "momentum_60d": momentum_60d,
                    "atr_percent": atr_percent,
                    "support_levels": support_levels,
                    "resistance_levels": resistance_levels,
                    "volume_analysis": {
                        "avg_volume": avg_volume,
                        "recent_volume": recent_volume,
                        "volume_trend": volume_trend
                    }
                },
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"GPT-4分析股票时出错 {symbol}: {str(e)}")
            return {
                "quantitative_metrics": {
                    "annual_return": 0.0,
                    "volatility": 0.0,
                    "sharpe_ratio": 0.0,
                    "momentum_20d": 0.0,
                    "momentum_60d": 0.0,
                    "atr_percent": 0.0,
                    "support_levels": [0.0, 0.0, 0.0],
                    "resistance_levels": [0.0, 0.0, 0.0],
                    "volume_analysis": {
                        "avg_volume": 0.0,
                        "recent_volume": 0.0,
                        "volume_trend": "未知"
                    }
                },
                "analysis": "无法生成分析"
            }

    async def analyze_investment(self, symbols: List[str]) -> Dict[str, Any]:
        """分析投资标的并生成建议"""
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
                    "predictions": {},
                    "gptAnalysis": {},
                    "charts": []
                }
            }
            
            # 处理输入的股票代码
            processed_symbols = []
            for symbol in symbols:
                try:
                    # 转换公司名称为股票代码
                    processed_symbol = self._convert_to_symbol(symbol)
                    logger.info(f"Converting {symbol} to {processed_symbol}")
                    processed_symbols.append(processed_symbol)
                except Exception as e:
                    logger.error(f"Error processing symbol {symbol}: {str(e)}")
                    continue
            
            if not processed_symbols:
                raise ValueError("没有有效的股票代码可供分析")
            
            for symbol in processed_symbols:
                logger.info(f"Fetching data for {symbol}")
                try:
                    stock = self._fetch_stock_data(symbol)
                    if stock is None:
                        logger.error(f"无法获取股票数据: {symbol}")
                        continue
                    
                    # 获取历史数据和信息
                    hist = stock.history(period="1y")
                    if hist.empty:
                        logger.warning(f"No historical data for {symbol}")
                        continue
                        
                    info = stock.info
                    if not info:
                        logger.warning(f"No information available for {symbol}")
                        continue
                    
                    # 分析基本面数据
                    fundamentals = self._analyze_fundamentals(symbol, stock)
                    result["investmentAdvice"]["fundamentals"][symbol] = fundamentals
                    
                    # 分析公司信息
                    company_info = {
                        "name": info.get("longName", symbol),
                        "introduction": info.get("longBusinessSummary", "暂无简介"),
                        "industry": info.get("industry", "未知行业"),
                        "sector": info.get("sector", "未知板块"),
                        "website": info.get("website", ""),
                        "country": info.get("country", ""),
                        "employees": info.get("fullTimeEmployees", 0),
                        "mainBusinesses": [info.get("industry", "未知业务")]
                    }
                    result["investmentAdvice"]["companyInfo"][symbol] = company_info
                    
                    # 生成价格预测
                    prediction_result = self._predict_stock_price(hist)
                    result["investmentAdvice"]["predictions"][symbol] = prediction_result
                    
                    # 使用GPT-4进行深度分析
                    gpt_analysis = await self._analyze_stock_with_gpt4(
                        symbol, 
                        hist, 
                        fundamentals,
                        prediction_result["market_analysis"]
                    )
                    result["investmentAdvice"]["gptAnalysis"][symbol] = gpt_analysis
                    
                    # 生成图表数据
                    charts = self._generate_charts(symbol, hist, prediction_result)
                    result["investmentAdvice"]["charts"].extend(charts)
                    
                    # 生成投资建议
                    advice = self._generate_investment_advice(symbol, fundamentals)
                    if not result["investmentAdvice"]["advice"]:
                        result["investmentAdvice"]["advice"] = advice
                    else:
                        result["investmentAdvice"]["advice"] += f"\n\n{advice}"
                    
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {str(e)}")
                    continue
            
            if not result["investmentAdvice"]["fundamentals"]:
                raise ValueError("无法获取任何股票的数据")
            
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

    def _calculate_market_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """计算市场技术指标"""
        try:
            if hist.empty:
                return {}
                
            close = hist['Close']
            high = hist['High']
            low = hist['Low']
            volume = hist['Volume']
            
            # 趋势指标
            macd = MACD(close=close)
            adx = ADXIndicator(high=high, low=low, close=close)
            
            # 动量指标
            stoch = StochasticOscillator(high=high, low=low, close=close)
            
            # 成交量指标
            obv = OnBalanceVolumeIndicator(close=close, volume=volume)
            fi = ForceIndexIndicator(close=close, volume=volume)
            
            # 波动率指标
            atr = AverageTrueRange(high=high, low=low, close=close)
            
            # 计算各项指标的最新值
            indicators = {
                "trend": {
                    "macd": self._sanitize_float(macd.macd().iloc[-1]),
                    "macd_signal": self._sanitize_float(macd.macd_signal().iloc[-1]),
                    "macd_diff": self._sanitize_float(macd.macd_diff().iloc[-1]),
                    "adx": self._sanitize_float(adx.adx().iloc[-1]),
                    "adx_pos": self._sanitize_float(adx.adx_pos().iloc[-1]),
                    "adx_neg": self._sanitize_float(adx.adx_neg().iloc[-1])
                },
                "momentum": {
                    "stoch_k": self._sanitize_float(stoch.stoch().iloc[-1]),
                    "stoch_d": self._sanitize_float(stoch.stoch_signal().iloc[-1])
                },
                "volume": {
                    "obv": self._sanitize_float(obv.on_balance_volume().iloc[-1]),
                    "force_index": self._sanitize_float(fi.force_index().iloc[-1])
                },
                "volatility": {
                    "atr": self._sanitize_float(atr.average_true_range().iloc[-1])
                }
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算市场指标时出错: {str(e)}")
            return {}

    def _analyze_market_condition(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """分析市场状况"""
        try:
            if hist.empty:
                return {
                    "market_trend": "未知",
                    "volatility": "未知",
                    "strength": "未知",
                    "risk_level": "未知"
                }
            
            # 获取技术指标
            indicators = self._calculate_market_indicators(hist)
            if not indicators:
                return {
                    "market_trend": "未知",
                    "volatility": "未知",
                    "strength": "未知",
                    "risk_level": "未知"
                }
            
            # 分析趋势
            macd = indicators["trend"]["macd"]
            macd_signal = indicators["trend"]["macd_signal"]
            adx = indicators["trend"]["adx"]
            
            if macd > macd_signal and adx > 25:
                trend = "强势上涨"
            elif macd < macd_signal and adx > 25:
                trend = "强势下跌"
            elif macd > macd_signal:
                trend = "温和上涨"
            elif macd < macd_signal:
                trend = "温和下跌"
            else:
                trend = "横盘整理"
            
            # 分析波动性
            atr = indicators["volatility"]["atr"]
            avg_price = hist['Close'].mean()
            volatility_ratio = (atr / avg_price) * 100
            
            if volatility_ratio > 3:
                volatility = "高波动"
            elif volatility_ratio < 1:
                volatility = "低波动"
            else:
                volatility = "正常波动"
            
            # 分析市场强度
            stoch_k = indicators["momentum"]["stoch_k"]
            stoch_d = indicators["momentum"]["stoch_d"]
            obv = indicators["volume"]["obv"]
            
            if stoch_k > 80 and obv > 0:
                strength = "超买"
            elif stoch_k < 20 and obv < 0:
                strength = "超卖"
            elif stoch_k > stoch_d:
                strength = "走强"
            elif stoch_k < stoch_d:
                strength = "走弱"
            else:
                strength = "中性"
            
            # 评估风险水平
            if volatility == "高波动" and (strength in ["超买", "超卖"]):
                risk = "高风险"
            elif volatility == "低波动" and strength == "中性":
                risk = "低风险"
            else:
                risk = "中等风险"
            
            return {
                "market_trend": trend,
                "volatility": volatility,
                "strength": strength,
                "risk_level": risk
            }
            
        except Exception as e:
            logger.error(f"分析市场状况时出错: {str(e)}")
            return {
                "market_trend": "未知",
                "volatility": "未知",
                "strength": "未知",
                "risk_level": "未知"
            }

    def _predict_stock_price(self, hist: pd.DataFrame, prediction_days: int = 30) -> Dict[str, Any]:
        """预测股票价格"""
        try:
            if hist.empty:
                return {
                    "predicted_prices": [],
                    "prediction_dates": [],
                    "confidence": 0,
                    "technical_indicators": {},
                    "market_analysis": {}
                }
            
            # 计算技术指标
            close_prices = hist['Close']
            
            # 计算移动平均线
            sma_20 = SMAIndicator(close=close_prices, window=20)
            sma_50 = SMAIndicator(close=close_prices, window=50)
            ema_20 = EMAIndicator(close=close_prices, window=20)
            
            # 计算RSI
            rsi = RSIIndicator(close=close_prices, window=14)
            
            # 计算布林带
            bb = BollingerBands(close=close_prices, window=20, window_dev=2)
            
            # 计算市场指标
            market_indicators = self._calculate_market_indicators(hist)
            market_analysis = self._analyze_market_condition(hist)
            
            # 准备特征数据
            features = pd.DataFrame({
                'sma_20': sma_20.sma_indicator(),
                'sma_50': sma_50.sma_indicator(),
                'ema_20': ema_20.ema_indicator(),
                'rsi': rsi.rsi(),
                'bb_high': bb.bollinger_hband(),
                'bb_low': bb.bollinger_lband(),
                'volume': hist['Volume'],
                'close': close_prices,
                'macd': market_indicators['trend']['macd'],
                'adx': market_indicators['trend']['adx'],
                'stoch_k': market_indicators['momentum']['stoch_k'],
                'obv': market_indicators['volume']['obv'],
                'atr': market_indicators['volatility']['atr']
            }).dropna()
            
            if len(features) < 50:
                return {
                    "predicted_prices": [],
                    "prediction_dates": [],
                    "confidence": 0,
                    "technical_indicators": {},
                    "market_analysis": market_analysis
                }
            
            # 准备训练数据
            X = features[:-1].values
            y = features['close'].shift(-1).dropna().values
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            # 训练集成模型
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            
            rf_model.fit(X_train, y_train)
            gb_model.fit(X_train, y_train)
            
            # 准备预测数据
            last_data = features.iloc[-1:].values
            
            # 进行预测
            rf_predictions = []
            gb_predictions = []
            current_data = last_data
            
            for _ in range(prediction_days):
                rf_pred = rf_model.predict(current_data)[0]
                gb_pred = gb_model.predict(current_data)[0]
                
                # 集成预测结果
                prediction = (rf_pred + gb_pred) / 2
                rf_predictions.append(rf_pred)
                gb_predictions.append(gb_pred)
                
                # 更新特征用于下一次预测
                new_data = current_data.copy()
                new_data[0, -1] = prediction
                current_data = new_data
            
            # 生成预测日期
            last_date = hist.index[-1]
            prediction_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') 
                              for i in range(prediction_days)]
            
            # 计算预测置信度
            rf_confidence = rf_model.score(X_test, y_test)
            gb_confidence = gb_model.score(X_test, y_test)
            ensemble_confidence = (rf_confidence + gb_confidence) / 2
            
            # 获取最新的技术指标值
            technical_indicators = {
                "sma_20": self._sanitize_float(features['sma_20'].iloc[-1]),
                "sma_50": self._sanitize_float(features['sma_50'].iloc[-1]),
                "ema_20": self._sanitize_float(features['ema_20'].iloc[-1]),
                "rsi": self._sanitize_float(features['rsi'].iloc[-1]),
                "bb_upper": self._sanitize_float(features['bb_high'].iloc[-1]),
                "bb_lower": self._sanitize_float(features['bb_low'].iloc[-1])
            }
            
            return {
                "predicted_prices": [(rf_pred + gb_pred) / 2 for rf_pred, gb_pred in zip(rf_predictions, gb_predictions)],
                "prediction_dates": prediction_dates,
                "confidence": self._sanitize_float(ensemble_confidence),
                "technical_indicators": technical_indicators,
                "market_analysis": market_analysis
            }
            
        except Exception as e:
            logger.error(f"Error predicting stock price: {str(e)}")
            return {
                "predicted_prices": [],
                "prediction_dates": [],
                "confidence": 0,
                "technical_indicators": {},
                "market_analysis": {
                    "market_trend": "未知",
                    "volatility": "未知",
                    "strength": "未知",
                    "risk_level": "未知"
                }
            } 
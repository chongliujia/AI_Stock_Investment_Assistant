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
from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator, IchimokuIndicator, KSTIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannels
from ta.volume import OnBalanceVolumeIndicator, ForceIndexIndicator, ChaikinMoneyFlowIndicator, MFIIndicator
from ta.others import DailyReturnIndicator, CumulativeReturnIndicator
from prophet import Prophet

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
        """生成增强的图表数据"""
        try:
            if hist.empty:
                return []
            
            # 计算技术指标
            technical_indicators = self._calculate_technical_indicators(hist)
            
            # 基础样式配置
            chart_config = {
                "responsive": True,
                "maintainAspectRatio": False,
                "interaction": {
                    "intersect": False,
                    "mode": "index"
                },
                "plugins": {
                    "tooltip": {
                        "enabled": True,
                        "position": "nearest"
                    },
                    "legend": {
                        "position": "top",
                        "align": "center"
                    }
                }
            }
            
            # 1. 价格和预测图表
            price_chart = {
                "type": "line",
                "title": f"{symbol} 价格走势与预测",
                "labels": hist.index.strftime('%Y-%m-%d').tolist(),
                "datasets": [
                    {
                        "label": "收盘价",
                        "data": hist['Close'].tolist(),
                        "borderColor": "rgb(75, 192, 192)",
                        "fill": False,
                        "tension": 0.1
                    },
                    {
                        "label": "20日均线",
                        "data": technical_indicators['trend_indicators']['sma_20'],
                        "borderColor": "rgb(255, 159, 64)",
                        "borderDash": [5, 5],
                        "fill": False
                    },
                    {
                        "label": "50日均线",
                        "data": technical_indicators['trend_indicators']['sma_50'],
                        "borderColor": "rgb(54, 162, 235)",
                        "borderDash": [5, 5],
                        "fill": False
                    }
                ],
                "config": {
                    **chart_config,
                    "scales": {
                        "y": {
                            "title": {
                                "display": True,
                                "text": "价格"
                            }
                        }
                    }
                }
            }
            
            # 如果有预测数据，添加到价格图表
            if prediction_result and prediction_result.get('lstm_predictions'):
                price_chart["datasets"].append({
                    "label": "LSTM预测",
                    "data": [None] * len(hist) + prediction_result['lstm_predictions'],
                    "borderColor": "rgb(153, 102, 255)",
                    "borderDash": [5, 5],
                    "fill": False
                })
            
            if prediction_result and prediction_result.get('prophet_predictions'):
                price_chart["datasets"].append({
                    "label": "Prophet预测",
                    "data": [None] * len(hist) + prediction_result['prophet_predictions'],
                    "borderColor": "rgb(255, 99, 132)",
                    "borderDash": [5, 5],
                    "fill": False
                })
            
            # 2. 技术指标组合图表
            technical_chart = {
                "type": "line",
                "title": f"{symbol} 技术指标",
                "labels": hist.index.strftime('%Y-%m-%d').tolist()[-60:],  # 显示最近60天
                "datasets": [
                    {
                        "label": "RSI",
                        "data": technical_indicators['momentum_indicators']['rsi'],
                        "borderColor": "rgb(255, 99, 132)",
                        "yAxisID": "rsi"
                    },
                    {
                        "label": "MACD",
                        "data": technical_indicators['trend_indicators']['macd_line'],
                        "borderColor": "rgb(54, 162, 235)",
                        "yAxisID": "macd"
                    },
                    {
                        "label": "MACD信号",
                        "data": technical_indicators['trend_indicators']['macd_signal'],
                        "borderColor": "rgb(75, 192, 192)",
                        "yAxisID": "macd"
                    }
                ],
                "config": {
                    **chart_config,
                    "scales": {
                        "rsi": {
                            "position": "right",
                            "title": {
                                "display": True,
                                "text": "RSI"
                            },
                            "min": 0,
                            "max": 100
                        },
                        "macd": {
                            "position": "left",
                            "title": {
                                "display": True,
                                "text": "MACD"
                            }
                        }
                    }
                }
            }
            
            # 3. 波动率指标图表
            volatility_chart = {
                "type": "line",
                "title": f"{symbol} 波动率指标",
                "labels": hist.index.strftime('%Y-%m-%d').tolist()[-30:],  # 显示最近30天
                "datasets": [
                    {
                        "label": "布林带上轨",
                        "data": technical_indicators['volatility_indicators']['bb_high'],
                        "borderColor": "rgba(255, 99, 132, 0.8)",
                        "fill": False
                    },
                    {
                        "label": "布林带中轨",
                        "data": technical_indicators['volatility_indicators']['bb_mid'],
                        "borderColor": "rgba(54, 162, 235, 0.8)",
                        "fill": False
                    },
                    {
                        "label": "布林带下轨",
                        "data": technical_indicators['volatility_indicators']['bb_low'],
                        "borderColor": "rgba(75, 192, 192, 0.8)",
                        "fill": False
                    },
                    {
                        "label": "Keltner通道上轨",
                        "data": technical_indicators['volatility_indicators']['keltner_high'],
                        "borderColor": "rgba(153, 102, 255, 0.8)",
                        "borderDash": [5, 5],
                        "fill": False
                    },
                    {
                        "label": "Keltner通道下轨",
                        "data": technical_indicators['volatility_indicators']['keltner_low'],
                        "borderColor": "rgba(255, 159, 64, 0.8)",
                        "borderDash": [5, 5],
                        "fill": False
                    }
                ],
                "config": {
                    **chart_config,
                    "scales": {
                        "y": {
                            "title": {
                                "display": True,
                                "text": "价格"
                            }
                        }
                    }
                }
            }
            
            # 4. 成交量和资金流向图表
            volume_chart = {
                "type": "mixed",
                "title": f"{symbol} 成交量和资金流向",
                "labels": hist.index.strftime('%Y-%m-%d').tolist()[-30:],
                "datasets": [
                    {
                        "type": "bar",
                        "label": "成交量",
                        "data": hist['Volume'].tolist()[-30:],
                        "backgroundColor": "rgba(153, 102, 255, 0.5)",
                        "yAxisID": "volume"
                    },
                    {
                        "type": "line",
                        "label": "资金流量指标(MFI)",
                        "data": technical_indicators['volume_indicators']['mfi'],
                        "borderColor": "rgb(255, 99, 132)",
                        "yAxisID": "mfi"
                    },
                    {
                        "type": "line",
                        "label": "钱德动量(CMF)",
                        "data": technical_indicators['volume_indicators']['cmf'],
                        "borderColor": "rgb(54, 162, 235)",
                        "yAxisID": "cmf"
                    }
                ],
                "config": {
                    **chart_config,
                    "scales": {
                        "volume": {
                            "position": "left",
                            "title": {
                                "display": True,
                                "text": "成交量"
                            }
                        },
                        "mfi": {
                            "position": "right",
                            "title": {
                                "display": True,
                                "text": "MFI"
                            },
                            "min": 0,
                            "max": 100
                        },
                        "cmf": {
                            "position": "right",
                            "title": {
                                "display": True,
                                "text": "CMF"
                            },
                            "min": -1,
                            "max": 1
                        }
                    }
                }
            }
            
            return [price_chart, technical_chart, volatility_chart, volume_chart]
            
        except Exception as e:
            logger.error(f"生成图表时出错 {symbol}: {str(e)}")
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
            
            # 使用流式响应
            analysis = await self.llm_provider.generate_response_stream(prompt, model="gpt-4-turbo-preview")
            
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

    async def _predict_with_llm(self, hist: pd.DataFrame, technical_indicators: Dict[str, Any], days_to_predict: int = 30) -> Dict[str, Any]:
        """使用大模型进行价格预测"""
        try:
            # 准备最近的价格数据
            recent_prices = hist['Close'].tail(60).tolist()  # 最近60天数据
            current_price = recent_prices[-1]
            price_changes = [((p2 - p1) / p1) * 100 for p1, p2 in zip(recent_prices[:-1], recent_prices[1:])]
            avg_daily_change = sum(price_changes) / len(price_changes)
            volatility = np.std(price_changes)

            # 准备技术分析数据
            trend_indicators = technical_indicators['trend_indicators']
            momentum_indicators = technical_indicators['momentum_indicators']
            volatility_indicators = technical_indicators['volatility_indicators']
            volume_indicators = technical_indicators['volume_indicators']

            # 构建提示词
            prompt = f"""作为一个专业的量化分析师和市场预测专家，请基于以下详细的市场数据，预测未来{days_to_predict}天的股票价格走势。

当前市场状况：
1. 价格数据：
- 当前价格：${current_price:.2f}
- 平均日涨跌幅：{avg_daily_change:.2f}%
- 价格波动率：{volatility:.2f}%

2. 趋势指标：
- MACD线：{trend_indicators['macd_line']:.2f}
- MACD信号：{trend_indicators['macd_signal']:.2f}
- ADX (趋势强度)：{trend_indicators['adx']:.2f}
- 20日均线：{trend_indicators['sma_20']:.2f}
- 50日均线：{trend_indicators['sma_50']:.2f}

3. 动量指标：
- RSI：{momentum_indicators['rsi']:.2f}
- 随机指标K：{momentum_indicators['stoch_k']:.2f}
- 随机指标D：{momentum_indicators['stoch_d']:.2f}
- ROC：{momentum_indicators['roc']:.2f}

4. 波动率指标：
- 布林带上轨：{volatility_indicators['bb_high']:.2f}
- 布林带中轨：{volatility_indicators['bb_mid']:.2f}
- 布林带下轨：{volatility_indicators['bb_low']:.2f}
- ATR：{volatility_indicators['atr']:.2f}

5. 成交量指标：
- 资金流量(MFI)：{volume_indicators['mfi']:.2f}
- 钱德动量(CMF)：{volume_indicators['cmf']:.2f}
- 成交量趋势：{volume_indicators['force_index']:.2f}

基于以上数据：
1. 请分析当前市场趋势和可能的转折点
2. 评估支撑位和阻力位
3. 预测未来{days_to_predict}天的每日收盘价，以当前价格为基准
4. 为每个预测提供置信度评分（0-100）

请以JSON格式返回预测结果，格式如下：
{{
    "analysis": "市场分析总结",
    "support_levels": [支撑位1, 支撑位2],
    "resistance_levels": [阻力位1, 阻力位2],
    "predictions": [
        {{"day": 1, "price": 价格, "confidence": 置信度}},
        ...
    ]
}}"""

            # 使用GPT-4进行预测
            response = await self.llm_provider.generate_response(prompt, model="gpt-4-turbo-preview")
            
            try:
                # 解析JSON响应
                prediction_data = eval(response)
                
                # 提取预测价格和日期
                predicted_prices = [p['price'] for p in prediction_data['predictions']]
                confidence_scores = [p['confidence'] for p in prediction_data['predictions']]
                
                # 生成预测日期
                last_date = hist.index[-1]
                prediction_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') 
                                  for i in range(days_to_predict)]
                
                # 计算平均置信度
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                
                return {
                    "predicted_prices": predicted_prices,
                    "prediction_dates": prediction_dates,
                    "confidence": avg_confidence / 100,  # 转换为0-1范围
                    "support_levels": prediction_data['support_levels'],
                    "resistance_levels": prediction_data['resistance_levels'],
                    "analysis": prediction_data['analysis']
                }
                
            except Exception as e:
                logger.error(f"解析预测结果时出错: {str(e)}")
                return {
                    "predicted_prices": [],
                    "prediction_dates": [],
                    "confidence": 0,
                    "support_levels": [],
                    "resistance_levels": [],
                    "analysis": "无法解析预测结果"
                }
                
        except Exception as e:
            logger.error(f"LLM预测出错: {str(e)}")
            return {
                "predicted_prices": [],
                "prediction_dates": [],
                "confidence": 0,
                "support_levels": [],
                "resistance_levels": [],
                "analysis": "预测过程出错"
            }

    async def _predict_stock_price(self, hist: pd.DataFrame, prediction_days: int = 30) -> Dict[str, Any]:
        """预测股票价格"""
        try:
            if hist.empty:
                return {
                    "predicted_prices": [],
                    "prediction_dates": [],
                    "confidence": 0,
                    "technical_indicators": {},
                    "market_analysis": {},
                    "support_levels": [],
                    "resistance_levels": [],
                    "analysis": "无数据可供分析"
                }
            
            # 计算技术指标
            technical_indicators = self._calculate_technical_indicators(hist)
            market_analysis = self._analyze_market_condition(hist)
            
            # 使用LLM进行预测
            prediction_result = await self._predict_with_llm(hist, technical_indicators, prediction_days)
            
            return {
                **prediction_result,
                "technical_indicators": technical_indicators,
                "market_analysis": market_analysis
            }
            
        except Exception as e:
            logger.error(f"预测股票价格时出错: {str(e)}")
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
                },
                "support_levels": [],
                "resistance_levels": [],
                "analysis": "预测过程出错"
            }

    def _calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """计算扩展的技术指标"""
        try:
            close = hist['Close']
            high = hist['High']
            low = hist['Low']
            volume = hist['Volume']
            
            # 趋势指标
            sma_20 = SMAIndicator(close, window=20).sma_indicator()
            sma_50 = SMAIndicator(close, window=50).sma_indicator()
            ema_20 = EMAIndicator(close, window=20).ema_indicator()
            macd = MACD(close)
            adx = ADXIndicator(high, low, close)
            ichimoku = IchimokuIndicator(high, low)
            kst = KSTIndicator(close)
            
            # 动量指标
            rsi = RSIIndicator(close)
            stoch = StochasticOscillator(high, low, close)
            williams_r = WilliamsRIndicator(high, low, close)
            roc = ROCIndicator(close)
            
            # 波动率指标
            bollinger = BollingerBands(close)
            atr = AverageTrueRange(high, low, close)
            keltner = KeltnerChannels(high, low, close)
            
            # 成交量指标
            obv = OnBalanceVolumeIndicator(close, volume)
            fi = ForceIndexIndicator(close, volume)
            cmf = ChaikinMoneyFlowIndicator(high, low, close, volume)
            mfi = MFIIndicator(high, low, close, volume)
            
            # 收益率指标
            daily_return = DailyReturnIndicator(close)
            cumulative_return = CumulativeReturnIndicator(close)
            
            return {
                "trend_indicators": {
                    "sma_20": self._sanitize_float(sma_20.iloc[-1]),
                    "sma_50": self._sanitize_float(sma_50.iloc[-1]),
                    "ema_20": self._sanitize_float(ema_20.iloc[-1]),
                    "macd_line": self._sanitize_float(macd.macd().iloc[-1]),
                    "macd_signal": self._sanitize_float(macd.macd_signal().iloc[-1]),
                    "macd_diff": self._sanitize_float(macd.macd_diff().iloc[-1]),
                    "adx": self._sanitize_float(adx.adx().iloc[-1]),
                    "ichimoku_a": self._sanitize_float(ichimoku.ichimoku_a().iloc[-1]),
                    "ichimoku_b": self._sanitize_float(ichimoku.ichimoku_b().iloc[-1]),
                    "kst": self._sanitize_float(kst.kst().iloc[-1]),
                    "kst_sig": self._sanitize_float(kst.kst_sig().iloc[-1])
                },
                "momentum_indicators": {
                    "rsi": self._sanitize_float(rsi.rsi().iloc[-1]),
                    "stoch_k": self._sanitize_float(stoch.stoch().iloc[-1]),
                    "stoch_d": self._sanitize_float(stoch.stoch_signal().iloc[-1]),
                    "williams_r": self._sanitize_float(williams_r.williams_r().iloc[-1]),
                    "roc": self._sanitize_float(roc.roc().iloc[-1])
                },
                "volatility_indicators": {
                    "bb_high": self._sanitize_float(bollinger.bollinger_hband().iloc[-1]),
                    "bb_mid": self._sanitize_float(bollinger.bollinger_mavg().iloc[-1]),
                    "bb_low": self._sanitize_float(bollinger.bollinger_lband().iloc[-1]),
                    "atr": self._sanitize_float(atr.average_true_range().iloc[-1]),
                    "keltner_high": self._sanitize_float(keltner.keltner_channel_hband().iloc[-1]),
                    "keltner_mid": self._sanitize_float(keltner.keltner_channel_mband().iloc[-1]),
                    "keltner_low": self._sanitize_float(keltner.keltner_channel_lband().iloc[-1])
                },
                "volume_indicators": {
                    "obv": self._sanitize_float(obv.on_balance_volume().iloc[-1]),
                    "force_index": self._sanitize_float(fi.force_index().iloc[-1]),
                    "cmf": self._sanitize_float(cmf.chaikin_money_flow().iloc[-1]),
                    "mfi": self._sanitize_float(mfi.money_flow_index().iloc[-1])
                },
                "return_indicators": {
                    "daily_return": self._sanitize_float(daily_return.daily_return().iloc[-1]),
                    "cumulative_return": self._sanitize_float(cumulative_return.cumulative_return().iloc[-1])
                }
            }
        except Exception as e:
            logger.error(f"计算技术指标时出错: {str(e)}")
            return {}

    def _predict_with_prophet(self, hist: pd.DataFrame, days_to_predict: int = 30) -> List[float]:
        """使用Prophet进行价格预测"""
        try:
            # 准备数据
            df = pd.DataFrame({
                'ds': hist.index,
                'y': hist['Close']
            })
            
            # 创建和训练模型
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05
            )
            model.fit(df)
            
            # 创建预测日期
            future_dates = model.make_future_dataframe(periods=days_to_predict)
            forecast = model.predict(future_dates)
            
            # 返回预测结果
            predictions = forecast.tail(days_to_predict)['yhat'].tolist()
            return predictions
            
        except Exception as e:
            logger.error(f"Prophet预测出错: {str(e)}")
            return []

    async def analyze_market(self) -> Dict[str, Any]:
        """分析整体市场状况"""
        try:
            # 初始化基础结构
            result = {
                "market_overview": {},
                "hot_sectors": {},
                "news_summary": "",
                "potential_stocks": [],
                "market_sentiment": None,
                "analysis_report": "",
                "news_items": []
            }

            # 1. 首先获取主要市场指数数据
            indices = {
                'SPY': '^GSPC',  # S&P 500
                'QQQ': '^IXIC',  # NASDAQ
                'DIA': '^DJI',   # Dow Jones
            }
            
            for name, symbol in indices.items():
                stock = self._fetch_stock_data(symbol)
                if stock:
                    hist = stock.history(period="1y")
                    if not hist.empty:
                        result["market_overview"][name] = self._analyze_index(hist)
                        # 立即返回更新
                        yield result

            # 2. 分析热门行业板块
            sectors_data = await self._analyze_sectors()
            result["hot_sectors"] = sectors_data
            yield result

            # 3. 获取市场新闻和情绪
            news_data = await self._analyze_market_news()
            result["news_summary"] = news_data["summary"]
            result["news_items"] = news_data.get("news_items", [])
            yield result

            # 4. 寻找潜力股票
            potential_stocks = await self._find_potential_stocks()
            result["potential_stocks"] = potential_stocks
            yield result

            # 5. 生成市场情绪指标
            market_sentiment = self._calculate_market_sentiment(
                result["market_overview"],
                result["hot_sectors"],
                news_data
            )
            result["market_sentiment"] = market_sentiment
            yield result

            # 6. 最后生成分析报告
            analysis_report = await self._generate_market_report(
                result["market_overview"],
                result["hot_sectors"],
                market_sentiment,
                news_data
            )
            result["analysis_report"] = analysis_report
            yield result

        except Exception as e:
            logger.error(f"市场分析出错: {str(e)}")
            raise

    def _analyze_index(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """分析市场指数数据"""
        try:
            current = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            month_ago = hist['Close'].iloc[-22] if len(hist) >= 22 else hist['Close'].iloc[0]
            
            daily_change = ((current - prev_close) / prev_close) * 100
            monthly_change = ((current - month_ago) / month_ago) * 100
            
            # 计算波动率 (20日年化)
            returns = hist['Close'].pct_change()
            volatility = returns.std() * np.sqrt(252) * 100
            
            # 计算技术指标
            sma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            
            rsi = RSIIndicator(hist['Close']).rsi().iloc[-1]
            macd = MACD(hist['Close'])
            
            return {
                "current": current,
                "daily_change": daily_change,
                "monthly_change": monthly_change,
                "volatility": volatility,
                "sma20_diff": ((current - sma20) / sma20) * 100,
                "sma50_diff": ((current - sma50) / sma50) * 100,
                "rsi": rsi,
                "macd": macd.macd().iloc[-1]
            }
        except Exception as e:
            logger.error(f"分析指数数据时出错: {str(e)}")
            return {
                "current": 0,
                "daily_change": 0,
                "monthly_change": 0,
                "volatility": 0,
                "sma20_diff": 0,
                "sma50_diff": 0,
                "rsi": 0,
                "macd": 0
            }

    async def _fetch_macro_indicators(self) -> Dict[str, Dict[str, Any]]:
        """获取宏观经济指标"""
        try:
            # 这里可以集成其他数据源获取更多宏观指标
            indicators = {
                "GDP增长率": {"value": 0, "change": 0, "trend": "稳定"},
                "CPI同比": {"value": 0, "change": 0, "trend": "稳定"},
                "PPI同比": {"value": 0, "change": 0, "trend": "稳定"},
                "失业率": {"value": 0, "change": 0, "trend": "稳定"},
                "M2增速": {"value": 0, "change": 0, "trend": "稳定"},
                "社会融资规模": {"value": 0, "change": 0, "trend": "稳定"}
            }
            
            # 使用LLM分析宏观经济形势
            prompt = """基于当前市场数据，分析以下宏观经济指标的可能状态：
            1. GDP增长率
            2. CPI同比
            3. PPI同比
            4. 失业率
            5. M2增速
            6. 社会融资规模
            
            请给出每个指标的预估值、变化趋势和分析。
            """
            
            response = await self.llm_provider.generate_response(prompt)
            # 解析响应更新指标
            
            return indicators
        except Exception as e:
            logger.error(f"获取宏观指标时出错: {str(e)}")
            return {}

    async def _analyze_sectors(self) -> Dict[str, Dict[str, Any]]:
        """分析行业板块表现"""
        try:
            # 主要行业ETF
            sector_etfs = {
                "科技": "XLK",
                "金融": "XLF",
                "医疗": "XLV",
                "能源": "XLE",
                "原材料": "XLB",
                "工业": "XLI",
                "必需消费": "XLP",
                "非必需消费": "XLY",
                "房地产": "XLRE",
                "公用事业": "XLU"
            }
            
            sectors_data = {}
            for name, symbol in sector_etfs.items():
                stock = self._fetch_stock_data(symbol)
                if stock:
                    hist = stock.history(period="1m")
                    if not hist.empty:
                        sectors_data[name] = self._analyze_sector(hist)
            
            return sectors_data
        except Exception as e:
            logger.error(f"分析行业板块时出错: {str(e)}")
            return {}

    def _analyze_sector(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """分析单个行业板块数据"""
        try:
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            price_change = ((current_price - prev_price) / prev_price) * 100
            
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].mean()
            volume_change = ((current_volume - avg_volume) / avg_volume) * 100
            
            # 计算动量和技术指标
            returns = hist['Close'].pct_change()
            momentum = returns.mean() * 100
            
            rsi = RSIIndicator(hist['Close']).rsi().iloc[-1]
            macd = MACD(hist['Close'])
            macd_signal = "看多" if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] else "看空"
            
            adx = ADXIndicator(hist['High'], hist['Low'], hist['Close'])
            trend_strength = adx.adx().iloc[-1]
            
            # 判断趋势
            sma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if current_price > sma50 and sma20 > sma50:
                trend = "上升"
            elif current_price < sma50 and sma20 < sma50:
                trend = "下降"
            else:
                trend = "震荡"
            
            # 判断成交量趋势
            volume_sma5 = hist['Volume'].rolling(window=5).mean().iloc[-1]
            volume_sma20 = hist['Volume'].rolling(window=20).mean().iloc[-1]
            if volume_sma5 > volume_sma20:
                volume_trend = "放量"
            elif volume_sma5 < volume_sma20 * 0.8:
                volume_trend = "缩量"
            else:
                volume_trend = "平稳"
            
            return {
                "symbol": hist.name,
                "price_change": price_change,
                "volume_change": volume_change,
                "momentum": momentum,
                "rsi": rsi,
                "current_price": current_price,
                "macd_signal": macd_signal,
                "trend_strength": trend_strength,
                "trend": trend,
                "volume_trend": volume_trend
            }
        except Exception as e:
            logger.error(f"分析行业数据时出错: {str(e)}")
            return {}

    async def _analyze_market_news(self) -> Dict[str, Any]:
        """分析市场新闻和情绪"""
        try:
            news_items = []
            
            # 1. 从Yahoo Finance获取RSS新闻
            try:
                import feedparser
                # Yahoo Finance RSS feeds
                rss_urls = [
                    'https://finance.yahoo.com/news/rssindex',
                    'https://finance.yahoo.com/news/markets/rssindex'
                ]
                
                for url in rss_urls:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:5]:  # 获取最新的5条新闻
                        news_items.append({
                            'title': entry.title,
                            'summary': entry.summary,
                            'link': entry.link,
                            'published': entry.published,
                            'source': 'Yahoo Finance'
                        })
            except Exception as e:
                logger.error(f"获取Yahoo Finance新闻时出错: {str(e)}")

            # 2. 从Alpha Vantage获取新闻
            try:
                import requests
                alpha_vantage_key = "demo"  # 使用demo key或从配置中获取
                url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={alpha_vantage_key}&topics=finance,technology"
                
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if 'feed' in data:
                        for item in data['feed'][:5]:  # 获取最新的5条新闻
                            news_items.append({
                                'title': item.get('title', ''),
                                'summary': item.get('summary', ''),
                                'link': item.get('url', ''),
                                'published': item.get('time_published', ''),
                                'source': 'Alpha Vantage',
                                'sentiment': item.get('overall_sentiment_score', 0)
                            })
            except Exception as e:
                logger.error(f"获取Alpha Vantage新闻时出错: {str(e)}")

            # 3. 从Finnhub获取新闻
            try:
                finnhub_key = "demo"  # 使用demo key或从配置中获取
                url = f"https://finnhub.io/api/v1/news?category=general&token={finnhub_key}"
                
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for item in data[:5]:  # 获取最新的5条新闻
                        news_items.append({
                            'title': item.get('headline', ''),
                            'summary': item.get('summary', ''),
                            'link': item.get('url', ''),
                            'published': item.get('datetime', ''),
                            'source': 'Finnhub',
                            'sentiment': item.get('sentiment', 0)
                        })
            except Exception as e:
                logger.error(f"获取Finnhub新闻时出错: {str(e)}")

            # 如果没有获取到任何新闻，返回默认值
            if not news_items:
                return {
                    "summary": "无法获取市场新闻",
                    "sentiment_score": 0.5,
                    "news_items": []
                }

            # 使用LLM分析新闻并生成摘要
            prompt = f"""请分析以下市场新闻并生成一份简洁的摘要，重点关注对市场可能产生的影响：

新闻列表：
{chr(10).join([f"- {item['title']} ({item['source']})" for item in news_items])}

请提供：
1. 新闻要点总结
2. 可能对市场产生的影响
3. 需要重点关注的领域
"""
            
            # 使用流式响应
            news_summary = await self.llm_provider.generate_response_stream(prompt)
            
            # 计算整体情绪分数
            sentiment_scores = [item.get('sentiment', 0.5) for item in news_items if 'sentiment' in item]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
            
            return {
                "summary": news_summary,
                "sentiment_score": avg_sentiment,
                "news_items": news_items
            }
            
        except Exception as e:
            logger.error(f"分析市场新闻时出错: {str(e)}")
            return {
                "summary": "无法获取市场新闻",
                "sentiment_score": 0.5,
                "news_items": []
            }

    async def _find_potential_stocks(self) -> List[Dict[str, Any]]:
        """寻找潜力股票"""
        try:
            # 可以根据不同的筛选策略寻找潜力股
            stocks = []
            # 示例：筛选科技板块的股票
            tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMD']
            
            for symbol in tech_stocks:
                stock = self._fetch_stock_data(symbol)
                if stock:
                    hist = stock.history(period="3mo")
                    info = stock.info
                    
                    if not hist.empty:
                        momentum = hist['Close'].pct_change().mean() * 100
                        rsi = RSIIndicator(hist['Close']).rsi().iloc[-1]
                        
                        stock_data = {
                            "symbol": symbol,
                            "name": info.get('longName', symbol),
                            "sector": info.get('sector', '未知'),
                            "momentum": momentum,
                            "rsi": rsi,
                            "pe_ratio": info.get('trailingPE'),
                            "profit_margin": info.get('profitMargins', 0) * 100,
                            "current_price": hist['Close'].iloc[-1],
                            "volume": hist['Volume'].iloc[-1],
                            "market_cap": info.get('marketCap', 0),
                            "score": self._calculate_stock_score(momentum, rsi, info)
                        }
                        stocks.append(stock_data)
            
            # 按得分排序
            stocks.sort(key=lambda x: x['score'], reverse=True)
            return stocks[:10]  # 返回前10只股票
            
        except Exception as e:
            logger.error(f"寻找潜力股时出错: {str(e)}")
            return []

    def _calculate_stock_score(self, momentum: float, rsi: float, info: Dict[str, Any]) -> float:
        """计算股票综合得分"""
        try:
            score = 0
            
            # 动量得分 (30%)
            if momentum > 0:
                score += min(momentum, 10) * 3
            
            # RSI得分 (20%)
            if 40 <= rsi <= 60:
                score += 20
            elif 30 <= rsi < 40 or 60 < rsi <= 70:
                score += 15
            elif 20 <= rsi < 30 or 70 < rsi <= 80:
                score += 10
            
            # 基本面得分 (50%)
            pe_ratio = info.get('trailingPE', 0)
            profit_margin = info.get('profitMargins', 0)
            
            if 0 < pe_ratio <= 30:
                score += 25
            elif 30 < pe_ratio <= 50:
                score += 15
            
            if profit_margin > 0.2:
                score += 25
            elif 0.1 <= profit_margin <= 0.2:
                score += 15
            elif 0 < profit_margin < 0.1:
                score += 10
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"计算股票得分时出错: {str(e)}")
            return 0

    def _calculate_market_sentiment(
        self,
        market_overview: Dict[str, Any],
        hot_sectors: Dict[str, Any],
        news_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算市场情绪指标"""
        try:
            # 技术面情绪
            technical_score = 0
            if market_overview:
                avg_rsi = sum(m['rsi'] for m in market_overview.values()) / len(market_overview)
                avg_momentum = sum(m['daily_change'] for m in market_overview.values()) / len(market_overview)
                
                technical = {
                    "rsi": avg_rsi,
                    "macd": "看多" if avg_momentum > 0 else "看空",
                    "trend": "上涨" if avg_momentum > 1 else "下跌" if avg_momentum < -1 else "震荡",
                    "volume_trend": "放量" if any(s['volume_trend'] == "放量" for s in hot_sectors.values()) else "平稳",
                    "volatility": sum(m['volatility'] for m in market_overview.values()) / len(market_overview),
                    "score": 0
                }
                
                # 计算技术面得分
                if 40 <= avg_rsi <= 60:
                    technical_score += 30
                elif 30 <= avg_rsi < 40 or 60 < avg_rsi <= 70:
                    technical_score += 20
                
                if avg_momentum > 0:
                    technical_score += min(avg_momentum * 2, 20)
                
                technical["score"] = technical_score
            
            # 新闻情绪
            news_sentiment = {
                "overall": "中性",
                "score": news_data.get("sentiment_score", 0.5) * 100
            }
            
            # 计算综合情绪得分
            overall_score = (technical_score * 0.6 + news_sentiment["score"] * 0.4)
            
            return {
                "technical": technical,
                "news": news_sentiment,
                "overall_score": overall_score
            }
            
        except Exception as e:
            logger.error(f"计算市场情绪时出错: {str(e)}")
            return {
                "technical": {
                    "rsi": 50,
                    "macd": "未知",
                    "trend": "未知",
                    "volume_trend": "未知",
                    "volatility": 0,
                    "score": 0
                },
                "news": {
                    "overall": "未知",
                    "score": 50
                },
                "overall_score": 50
            }

    async def _generate_market_report(
        self,
        market_overview: Dict[str, Any],
        hot_sectors: Dict[str, Any],
        market_sentiment: Dict[str, Any],
        news_data: Dict[str, Any]
    ) -> str:
        """生成市场分析报告"""
        try:
            prompt = f"""请基于以下市场数据生成一份详细的市场分析报告：

1. 市场概览：
{market_overview}

2. 热门行业板块：
{hot_sectors}

3. 市场情绪：
技术面得分：{market_sentiment['technical']['score']}
新闻情绪得分：{market_sentiment['news']['score']}
综合情绪得分：{market_sentiment['overall_score']}

4. 市场新闻摘要：
{news_data['summary']}

请从以下几个方面进行分析：
1. 市场整体走势和关键技术位
2. 行业板块轮动分析
3. 市场情绪和投资者心理
4. 主要风险因素
5. 投资策略建议

请用专业但易懂的语言撰写报告。
"""
            
            # 使用流式响应
            report = await self.llm_provider.generate_response_stream(prompt)
            return report
            
        except Exception as e:
            logger.error(f"生成市场报告时出错: {str(e)}")
            return "无法生成市场分析报告" 
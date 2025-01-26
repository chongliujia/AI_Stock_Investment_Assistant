import React, { useState, useEffect, useCallback } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface ChartDataset {
  label: string;
  data: number[];
  borderColor?: string;
  backgroundColor?: string;
  tension?: number;
  borderDash?: number[];
}

interface ChartData {
  type: string;
  title: string;
  labels: string[];
  datasets: ChartDataset[];
}

interface FundamentalMetrics {
  basic_metrics: {
    current_price: number;
    price_change: number;
    avg_volume: number;
    volume_change: number;
    price_to_sma20: number;
  };
  valuation_metrics: {
    market_cap: number;
    pe_ratio: number;
    forward_pe: number;
    peg_ratio: number;
    price_to_book: number;
    valuation_status: string;
  };
  profitability_metrics: {
    profit_margin: number;
    operating_margin: number;
    dividend_yield: number;
  };
  risk_metrics: {
    beta: number;
    risk_level: string;
  };
}

interface MarketAnalysis {
  market_trend: string;
  volatility: string;
  strength: string;
  risk_level: string;
}

interface PredictionData {
  predicted_prices: number[];
  prediction_dates: string[];
  confidence: number;
  technical_indicators: {
    rsi: number;
    sma_20: number;
    sma_50: number;
    bb_upper: number;
    bb_lower: number;
    ema_20: number;
  };
  market_analysis: MarketAnalysis;
}

interface QuantitativeMetrics {
  annual_return: number;
  volatility: number;
  sharpe_ratio: number;
  momentum_20d: number;
  momentum_60d: number;
  atr_percent: number;
  support_levels: number[];
  resistance_levels: number[];
  volume_analysis: {
    avg_volume: number;
    recent_volume: number;
    volume_trend: string;
  };
}

interface GPTAnalysis {
  quantitative_metrics: QuantitativeMetrics;
  analysis: string;
}

interface InvestmentAdviceData {
  advice: string;
  companyInfo: {
    [key: string]: {
      name: string;
      introduction: string;
      industry: string;
      sector: string;
      website: string;
      country: string;
      employees: number;
      mainBusinesses: string[];
    };
  };
  fundamentals: {
    [key: string]: FundamentalMetrics;
  };
  predictions: {
    [key: string]: PredictionData;
  };
  gptAnalysis: {
    [key: string]: GPTAnalysis;
  };
  charts: ChartData[];
}

interface AnalysisResult {
  stockAnalysis: ChartData;
  investmentAdvice: InvestmentAdviceData;
}

interface InvestmentAnalysisProps {
  initialQuery?: string;
}

function LoadingSpinner() {
  return (
    <div className="flex justify-center items-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>
  );
}

// 添加防抖函数
const debounce = (func: Function, wait: number) => {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: any[]) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

function InvestmentAnalysis({ initialQuery = '' }: InvestmentAnalysisProps) {
  const [query, setQuery] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 从本地存储加载最近搜索记录
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  // 优化搜索记录的保存
  const saveSearch = useCallback((search: string) => {
    try {
      const saved = localStorage.getItem('recentSearches');
      const searches = saved ? JSON.parse(saved) : [];
      const updated = [search, ...searches.filter((savedSearch: string) => savedSearch !== search)].slice(0, 5);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
      setRecentSearches(updated);
    } catch (err) {
      console.error('Error saving search history:', err);
    }
  }, []);

  // 优化分析处理函数
  const handleAnalysis = async () => {
    if (!query.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // 处理输入的股票代码
      const rawSymbols = query.trim().split(/[,，\s]+/).filter(Boolean);
      
      // 验证输入
      if (rawSymbols.length === 0) {
        throw new Error('请输入有效的股票代码或公司名称');
      }
      
      if (rawSymbols.length > 5) {
        throw new Error('一次最多只能分析5支股票');
      }
      
      // 规范化股票代码
      const symbols = rawSymbols.map(symbol => {
        // 移除特殊字符
        const cleaned = symbol.replace(/[^\w\s]/g, '').trim();
        // 如果是纯数字，可能是A股代码，需要特殊处理
        if (/^\d+$/.test(cleaned)) {
          if (cleaned.length === 6) {
            // A股代码处理
            const prefix = cleaned.startsWith('6') ? 'sh' : 'sz';
            return `${prefix}${cleaned}`;
          }
        }
        return cleaned;
      });
      
      console.log('Analyzing symbols:', symbols);
      
      const response = await fetch('/api/analyze-investment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbols }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || data.message || '分析请求失败');
      }

      if (!data.data?.investmentAdvice?.advice) {
        console.error('Invalid response format:', data);
        throw new Error('返回数据格式不正确');
      }

      setResult(data.data);
      saveSearch(query.trim());
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : '分析过程中出错');
      setResult(null);
    } finally {
      setLoading(false);
      setIsSubmitting(false);
    }
  };

  // 优化键盘事件处理
  useEffect(() => {
    const debouncedAnalysis = debounce(() => {
      if (query.trim()) {
        handleAnalysis();
      }
    }, 300);

    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === 'Enter' && !event.shiftKey && !isSubmitting) {
        event.preventDefault();
        debouncedAnalysis();
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => {
      window.removeEventListener('keypress', handleKeyPress);
    };
  }, [query, isSubmitting]);

  // 当initialQuery改变时更新query
  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
      handleAnalysis();
    }
  }, [initialQuery]);

  // 渲染图表
  const renderChart = useCallback((chart: ChartData, index: number) => {
    if (chart.type === 'line') {
      return (
        <div key={index} className="card">
          <h3 className="text-xl font-bold mb-4">{chart.title}</h3>
          <div className="h-80">
            <Line
              data={{
                labels: chart.labels,
                datasets: chart.datasets
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top',
                  }
                },
                scales: {
                  y: {
                    beginAtZero: false
                  }
                }
              }}
            />
          </div>
        </div>
      );
    }
    return null;
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">智能投资分析</h1>
          
          {/* 搜索区域 */}
          <div className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAnalysis()}
                  placeholder="输入股票代码或公司名称（例如：AAPL 或 Apple）"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {query && (
                  <button
                    onClick={() => setQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
              <button
                onClick={handleAnalysis}
                disabled={isSubmitting || !query.trim()}
                className={`px-8 py-3 rounded-lg font-medium text-white transition-colors ${
                  isSubmitting || !query.trim() 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {isSubmitting ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                    <span>分析中...</span>
                  </div>
                ) : (
                  <span>开始分析</span>
                )}
              </button>
            </div>

            {/* 最近搜索 */}
            {recentSearches.length > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500">最近搜索：</span>
                <div className="flex flex-wrap gap-2">
                  {recentSearches.map((search, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setQuery(search);
                        handleAnalysis();
                      }}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
                    >
                      {search}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 错误信息 */}
        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* 分析结果 */}
        {result && (
          <div className="space-y-8">
            {/* 投资建议卡片 */}
            <div className="bg-white rounded-lg shadow-sm overflow-hidden">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">投资建议</h2>
                <div className="prose max-w-none">
                  <div className="bg-gray-50 rounded-lg p-6">
                    <pre className="whitespace-pre-wrap font-sans text-gray-700">
                      {result.investmentAdvice.advice}
                    </pre>
                  </div>
                </div>
              </div>
            </div>

            {/* 公司信息卡片 */}
            {result.investmentAdvice?.companyInfo && 
              Object.entries(result.investmentAdvice.companyInfo).map(([symbol, info]) => (
                <div key={symbol} className="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-bold text-gray-900">{info.name}</h2>
                      <span className="text-lg font-semibold text-blue-600">{symbol}</span>
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">公司介绍</h3>
                        <p className="text-gray-700 leading-relaxed">{info.introduction}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-6">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-3">基本信息</h3>
                          <dl className="space-y-2">
                            <div>
                              <dt className="text-sm text-gray-500">行业</dt>
                              <dd className="text-gray-900">{info.industry}</dd>
                            </div>
                            <div>
                              <dt className="text-sm text-gray-500">板块</dt>
                              <dd className="text-gray-900">{info.sector}</dd>
                            </div>
                          </dl>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-3">其他信息</h3>
                          <dl className="space-y-2">
                            <div>
                              <dt className="text-sm text-gray-500">国家/地区</dt>
                              <dd className="text-gray-900">{info.country}</dd>
                            </div>
                            <div>
                              <dt className="text-sm text-gray-500">员工数量</dt>
                              <dd className="text-gray-900">{info.employees.toLocaleString()}</dd>
                            </div>
                          </dl>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

            {/* 基本面数据卡片 */}
            <div className="bg-white rounded-lg shadow-sm overflow-hidden">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">基本面数据</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr className="bg-gray-50">
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">股票</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">当前价格</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">市值(B$)</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">市盈率</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">预期市盈率</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">利润率(%)</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">股息率(%)</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Beta系数</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">估值状态</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {result.investmentAdvice?.fundamentals && 
                        Object.entries(result.investmentAdvice.fundamentals).map(([symbol, data]) => (
                          <tr key={symbol} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{symbol}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700">${data.basic_metrics.current_price.toFixed(2)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700">{data.valuation_metrics.market_cap.toFixed(2)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700">{data.valuation_metrics.pe_ratio.toFixed(2)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700">{data.valuation_metrics.forward_pe.toFixed(2)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700">{data.profitability_metrics.profit_margin.toFixed(2)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700">{data.profitability_metrics.dividend_yield.toFixed(2)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700">{data.risk_metrics.beta.toFixed(2)}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                data.valuation_metrics.valuation_status === '高估' ? 'bg-red-100 text-red-800' :
                                data.valuation_metrics.valuation_status === '低估' ? 'bg-green-100 text-green-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                {data.valuation_metrics.valuation_status}
                              </span>
                            </td>
                          </tr>
                        ))
                      }
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* 图表展示 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {result.investmentAdvice?.charts?.map((chart, index) => (
                <div key={index} className="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div className="p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">{chart.title}</h3>
                    <div className="h-[400px]">
                      {chart.type === 'line' && (
                        <Line
                          data={{
                            labels: chart.labels,
                            datasets: chart.datasets.map(dataset => ({
                              ...dataset,
                              borderWidth: 2,
                              pointRadius: 1,
                              tension: 0.4
                            }))
                          }}
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                              intersect: false,
                              mode: 'index'
                            },
                            plugins: {
                              legend: {
                                position: 'top',
                                labels: {
                                  usePointStyle: true,
                                  padding: 20
                                }
                              },
                              tooltip: {
                                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                                titleColor: '#1f2937',
                                bodyColor: '#4b5563',
                                borderColor: '#e5e7eb',
                                borderWidth: 1,
                                padding: 12,
                                displayColors: false
                              }
                            },
                            scales: {
                              y: {
                                beginAtZero: false,
                                grid: {
                                  color: 'rgba(0, 0, 0, 0.05)'
                                }
                              },
                              x: {
                                grid: {
                                  display: false
                                }
                              }
                            }
                          }}
                        />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* GPT-4 分析结果 */}
            {result.investmentAdvice?.gptAnalysis && 
              Object.entries(result.investmentAdvice.gptAnalysis).map(([symbol, analysis]) => (
                <div key={symbol} className="bg-white rounded-lg shadow-sm overflow-hidden">
                  <div className="p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">{symbol} GPT-4 深度分析</h2>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                      {/* 量化指标 */}
                      <div className="bg-gray-50 rounded-lg p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">量化指标</h3>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">年化收益率</span>
                            <span className={`font-medium ${
                              analysis.quantitative_metrics.annual_return >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {(analysis.quantitative_metrics.annual_return * 100).toFixed(2)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">年化波动率</span>
                            <span className={`font-medium ${
                              analysis.quantitative_metrics.volatility <= 0.2 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {(analysis.quantitative_metrics.volatility * 100).toFixed(2)}%
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">夏普比率</span>
                            <span className={`font-medium ${
                              analysis.quantitative_metrics.sharpe_ratio >= 1 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {analysis.quantitative_metrics.sharpe_ratio.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* 技术水平 */}
                      <div className="bg-gray-50 rounded-lg p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">技术水平</h3>
                        <div className="grid grid-cols-2 gap-6">
                          <div>
                            <h4 className="font-medium text-gray-700 mb-3">支撑位</h4>
                            <div className="space-y-2">
                              {analysis.quantitative_metrics.support_levels.map((level, index) => (
                                <div key={index} className="flex justify-between items-center">
                                  <span className="text-gray-600">
                                    {index === 0 ? '强' : index === 1 ? '中' : '弱'}支撑
                                  </span>
                                  <span className="font-medium text-gray-900">
                                    ${level.toFixed(2)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-700 mb-3">阻力位</h4>
                            <div className="space-y-2">
                              {analysis.quantitative_metrics.resistance_levels.map((level, index) => (
                                <div key={index} className="flex justify-between items-center">
                                  <span className="text-gray-600">
                                    {index === 0 ? '强' : index === 1 ? '中' : '弱'}阻力
                                  </span>
                                  <span className="font-medium text-gray-900">
                                    ${level.toFixed(2)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 分析结论 */}
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">分析结论</h3>
                      <div className="prose max-w-none">
                        <pre className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed">
                          {analysis.analysis}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default InvestmentAnalysis; 
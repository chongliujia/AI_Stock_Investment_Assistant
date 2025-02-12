import React, { useState, useEffect } from 'react';
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
  Filler,
  ScriptableContext
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { useTheme } from '../hooks/useTheme';
import ChartComponent from './ChartComponent';
import { ErrorBoundary } from 'react-error-boundary';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface MarketData {
  current: number;
  daily_change: number;
  monthly_change: number;
  volatility: number;
  sma20_diff: number;
  sma50_diff: number;
  rsi: number;
  macd: number;
}

interface SectorData {
  symbol: string;
  price_change: number;
  volume_change: number;
  momentum: number;
  rsi: number;
  current_price: number;
  macd_signal: string;
  trend_strength: number;
  trend: string;
  volume_trend: string;
}

interface PotentialStock {
  symbol: string;
  name: string;
  sector: string;
  momentum: number;
  rsi: number;
  pe_ratio: number | null;
  profit_margin: number | null;
  score: number;
  current_price: number;
  volume: number;
  market_cap: number;
}

interface MarketSentiment {
  technical: {
    rsi: number;
    macd: string;
    trend: string;
    volume_trend: string;
    volatility: number;
    score: number;
  };
  news: {
    overall: string;
    score: number;
  };
  overall_score: number;
}

interface ChartData {
  type: 'line' | 'bar' | 'mixed';
  title: string;
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    fill?: boolean;
    type?: 'line' | 'bar';
  }>;
  config: any;
}

interface MarketAnalysisProps {
  onAnalyze: () => void;
  result: {
    market_overview?: {
      [key: string]: {
        current: number;
        daily_change: number;
        monthly_change: number;
        volatility: number;
        sma20_diff: number;
        sma50_diff: number;
        rsi: number;
        macd: number;
      };
    };
    hot_sectors?: {
      [key: string]: {
        price_change: number;
        volume_change: number;
        momentum: number;
        rsi: number;
        current_price: number;
        macd_signal: string;
        trend_strength: number;
        trend: string;
        volume_trend: string;
      };
    };
    news_summary?: string;
    potential_stocks?: Array<{
      symbol: string;
      name: string;
      sector: string;
      momentum: number;
      rsi: number;
      pe_ratio: number;
      profit_margin: number;
      current_price: number;
      volume: number;
      market_cap: number;
      score: number;
    }>;
    market_sentiment?: {
      technical: {
        rsi: number;
        macd: string;
        trend: string;
        volume_trend: string;
        volatility: number;
        score: number;
      };
      news: {
        overall: string;
        score: number;
      };
      overall_score: number;
    };
    analysis_report?: string;
    news_items?: Array<{
      title: string;
      summary: string;
      link: string;
      published: string;
      source: string;
      sentiment?: number;
    }>;
    charts?: ChartData[];
  } | null;
  loading: boolean;
}

// 自定义错误边界组件
const ChartErrorBoundary: React.FC<{
  children: React.ReactNode;
  onError?: (error: Error) => void;
}> = ({ children, onError }) => {
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      setHasError(true);
      setError(event.error);
      onError?.(event.error);
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, [onError]);

  if (hasError) {
    return (
      <div className="absolute inset-0 flex items-center justify-center text-red-500">
        <div className="text-center">
          <p className="font-semibold">图表渲染失败</p>
          {error && <p className="text-sm">{error.message}</p>}
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

const MarketAnalysis: React.FC<MarketAnalysisProps> = ({ onAnalyze, result, loading }) => {
  const { theme } = useTheme();
  console.log('MarketAnalysis rendering with result:', result);

  useEffect(() => {
    console.log('MarketAnalysis mounted');
  }, []);

  const getChartType = (type: string): 'line' | 'bar' => {
    if (type === 'line' || type === 'bar') {
      return type;
    }
    return 'bar'; // 默认返回 'bar' 类型
  };

  const renderMarketOverview = () => {
    if (!result?.market_overview) {
      console.log('No market overview data available');
      return null;
    }

    console.log('Rendering market overview with data:', result.market_overview);
    return (
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">市场概览</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(result.market_overview).map(([name, data]) => (
            <div key={name} className="border p-4 rounded-lg shadow-sm">
              <h4 className="font-medium text-lg mb-2">{name}</h4>
              <div className="space-y-2">
                <p className={`text-lg font-semibold ${
                  data.daily_change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {data.current.toFixed(2)}
                  <span className="ml-2">
                    ({data.daily_change >= 0 ? '+' : ''}{data.daily_change.toFixed(2)}%)
                  </span>
                </p>
                <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <p>月度变化: {data.monthly_change.toFixed(2)}%</p>
                  <p>波动率: {data.volatility.toFixed(2)}%</p>
                  <p>RSI: {data.rsi.toFixed(2)}</p>
                  <p>MACD: {data.macd.toFixed(2)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderMarketSentiment = () => {
    if (!result?.market_sentiment) {
      console.log('No market sentiment data available');
      return null;
    }

    console.log('Rendering market sentiment with data:', result.market_sentiment);
    const { technical, news, overall_score } = result.market_sentiment;

    return (
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">市场情绪</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 技术面情绪 */}
          <div className={`p-4 rounded-lg ${
            theme === 'dark' ? 'bg-gray-800' : 'bg-white'
          } shadow-sm`}>
            <h4 className="font-medium mb-3">技术面情绪</h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">RSI</span>
                <span className="font-medium">{technical.rsi.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">MACD信号</span>
                <span className="font-medium">{technical.macd}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">趋势</span>
                <span className="font-medium">{technical.trend}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">成交量趋势</span>
                <span className="font-medium">{technical.volume_trend}</span>
              </div>
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2.5 mb-1">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full" 
                    style={{ width: `${technical.score}%` }}
                  ></div>
                </div>
                <div className="text-sm text-right">得分: {technical.score.toFixed(0)}</div>
              </div>
            </div>
          </div>

          {/* 新闻情绪 */}
          <div className={`p-4 rounded-lg ${
            theme === 'dark' ? 'bg-gray-800' : 'bg-white'
          } shadow-sm`}>
            <h4 className="font-medium mb-3">新闻情绪</h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">整体情绪</span>
                <span className="font-medium">{news.overall}</span>
              </div>
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2.5 mb-1">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full" 
                    style={{ width: `${news.score}%` }}
                  ></div>
                </div>
                <div className="text-sm text-right">得分: {news.score.toFixed(0)}</div>
              </div>
            </div>
          </div>

          {/* 综合情绪 */}
          <div className={`p-4 rounded-lg ${
            theme === 'dark' ? 'bg-gray-800' : 'bg-white'
          } shadow-sm`}>
            <h4 className="font-medium mb-3">综合情绪</h4>
            <div className="flex flex-col items-center justify-center h-full">
              <div className="relative w-32 h-32">
                <svg className="w-full h-full" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#E5E7EB"
                    strokeWidth="3"
                  />
                  <path
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#3B82F6"
                    strokeWidth="3"
                    strokeDasharray={`${overall_score}, 100`}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold">{overall_score.toFixed(0)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderHotSectors = () => {
    if (!result?.hot_sectors) {
      console.log('No hot sectors data available');
      return null;
    }

    console.log('Rendering hot sectors with data:', result.hot_sectors);
    return (
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">热门行业板块</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(result.hot_sectors).map(([name, data]) => (
            <div key={name} className={`border rounded-lg shadow-sm p-4 
              ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <h4 className="font-medium text-lg mb-2">{name}</h4>
              <div className="space-y-2">
                <p className={`text-lg font-semibold ${
                  data.price_change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {data.price_change >= 0 ? '+' : ''}{data.price_change.toFixed(2)}%
                </p>
                <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} space-y-1`}>
                  <p>成交量变化: {data.volume_change.toFixed(2)}%</p>
                  <p>动量: {data.momentum.toFixed(2)}</p>
                  <p>RSI: {data.rsi.toFixed(2)}</p>
                  <p>趋势: {data.trend}</p>
                  <p>成交量趋势: {data.volume_trend}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderNews = () => {
    if (!result?.news_items || result.news_items.length === 0) {
      console.log('No news data available');
      return null;
    }

    console.log('Rendering news with data:', result.news_items);
    return (
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">市场新闻</h3>
        <div className="space-y-4">
          {result.news_items.map((news, index) => (
            <div key={index} className={`p-4 rounded-lg ${
              theme === 'dark' ? 'bg-gray-800' : 'bg-white'
            } shadow-sm`}>
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium text-lg">{news.title}</h4>
                {news.sentiment !== undefined && (
                  <span className={`px-2 py-1 text-sm rounded ${
                    news.sentiment > 0.6 ? 'bg-green-100 text-green-800' :
                    news.sentiment < 0.4 ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {news.sentiment > 0.6 ? '积极' :
                     news.sentiment < 0.4 ? '消极' : '中性'}
                  </span>
                )}
              </div>
              <p className={`text-sm mb-2 ${
                theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {news.summary}
              </p>
              <div className="flex justify-between items-center text-sm">
                <span className={theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}>
                  {news.source}
                </span>
                <a 
                  href={news.link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-600"
                >
                  阅读更多
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderPotentialStocks = () => {
    if (!result?.potential_stocks || result.potential_stocks.length === 0) {
      console.log('No potential stocks data available');
      return null;
    }

    console.log('Rendering potential stocks with data:', result.potential_stocks);
    return (
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">潜力股票</h3>
        <div className="overflow-x-auto">
          <table className={`min-w-full divide-y ${
            theme === 'dark' ? 'divide-gray-700' : 'divide-gray-200'
          }`}>
            <thead className={theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'}>
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">股票</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">行业</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">价格</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">动量</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">RSI</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">市盈率</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">评分</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${
              theme === 'dark' ? 'divide-gray-700' : 'divide-gray-200'
            }`}>
              {result.potential_stocks.map((stock, index) => (
                <tr key={stock.symbol} className={
                  theme === 'dark' 
                    ? index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-900'
                    : index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                }>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="font-medium">{stock.symbol}</div>
                        <div className="text-sm text-gray-500">{stock.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{stock.sector}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">${stock.current_price.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={stock.momentum >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {stock.momentum.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{stock.rsi.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {stock.pe_ratio ? stock.pe_ratio.toFixed(2) : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2.5">
                        <div 
                          className="bg-blue-600 h-2.5 rounded-full" 
                          style={{ width: `${stock.score}%` }}
                        ></div>
                      </div>
                      <span className="ml-2 text-sm">{stock.score.toFixed(0)}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderCharts = () => {
    if (!result?.charts || !Array.isArray(result.charts)) {
      console.log('No charts data available');
      return null;
    }

    console.log('Rendering charts with data:', result.charts);
    return (
      <div className="space-y-8">
        {result.charts.map((chart, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">{chart.title}</h3>
            <div className="h-96 relative">
              <ChartErrorBoundary
                onError={(error) => {
                  console.error('Chart rendering error:', error);
                }}
              >
                <ChartComponent
                  type={getChartType(chart.type)}
                  data={{
                    labels: chart.labels,
                    datasets: chart.datasets.map(dataset => ({
                      ...dataset,
                      type: dataset.type ? getChartType(dataset.type) : undefined,
                      borderColor: dataset.borderColor || (theme === 'dark' ? '#fff' : '#666'),
                      backgroundColor: dataset.backgroundColor || (theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)')
                    }))
                  }}
                  options={{
                    ...chart.config,
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      ...chart.config.plugins,
                      legend: {
                        ...chart.config.plugins?.legend,
                        labels: {
                          ...chart.config.plugins?.legend?.labels,
                          color: theme === 'dark' ? '#fff' : '#666'
                        }
                      }
                    },
                    scales: {
                      ...chart.config.scales,
                      x: {
                        ...chart.config.scales?.x,
                        grid: {
                          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                          color: theme === 'dark' ? '#fff' : '#666'
                        }
                      },
                      y: {
                        ...chart.config.scales?.y,
                        grid: {
                          color: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                          color: theme === 'dark' ? '#fff' : '#666'
                        }
                      }
                    }
                  }}
                />
              </ChartErrorBoundary>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
      {/* 顶部按钮和加载状态 */}
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={onAnalyze}
          disabled={loading}
          className={`px-4 py-2 rounded-md transition-colors duration-200 disabled:opacity-50
            ${theme === 'dark' 
              ? 'bg-blue-600 hover:bg-blue-700 text-white' 
              : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
        >
          {loading ? '分析中...' : '开始分析'}
        </button>
      </div>

      {/* 加载状态显示 */}
      {loading && (
        <div className="text-center py-8">
          <div className={`animate-spin rounded-full h-12 w-12 border-b-2 
            ${theme === 'dark' ? 'border-blue-400' : 'border-blue-500'} 
            mx-auto mb-4`}
          ></div>
          <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
            正在分析市场数据，请稍候...
          </p>
        </div>
      )}

      {/* 错误显示 */}
      {!loading && !result && (
        <div className="text-center py-8">
          <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
            点击"开始分析"按钮开始市场分析
          </p>
        </div>
      )}

      {/* 结果显示 */}
      {!loading && result && (
        <div className="space-y-8">
          {renderMarketOverview()}
          {renderMarketSentiment()}
          {renderHotSectors()}
          {renderNews()}
          {renderPotentialStocks()}
          {renderCharts()}
          
          {/* 市场分析报告 */}
          {result.analysis_report && (
            <div className={`p-6 rounded-lg shadow ${
              theme === 'dark' ? 'bg-gray-800' : 'bg-white'
            }`}>
              <h3 className="text-lg font-semibold mb-4">市场分析报告</h3>
              <div className={`prose max-w-none ${
                theme === 'dark' ? 'prose-invert' : ''
              }`}>
                <p className="whitespace-pre-wrap">{result.analysis_report}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MarketAnalysis;
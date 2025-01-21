import React, { useState } from 'react';
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
  change: number;
  volume_change: number;
}

interface PotentialStock {
  symbol: string;
  name: string;
  sector: string;
  industry: string;
  technical_indicators: {
    rsi: number;
    macd: number;
    sma_20: number;
    sma_50: number;
    close: number;
  };
  momentum_indicators: {
    price_momentum: number;
    volume_momentum: number;
  };
  fundamental_indicators: {
    pe_ratio: number;
    pb_ratio: number;
    profit_margin: number;
    revenue_growth: number;
    debt_to_equity: number;
    current_ratio: number;
  };
  scores: {
    technical_score: number;
    momentum_score: number;
    fundamental_score: number;
  };
  total_score: number;
}

interface MarketAnalysisProps {
  onAnalyze: () => Promise<void>;
  result: {
    market_overview: { [key: string]: MarketData };
    hot_sectors: { [key: string]: SectorData };
    macro_indicators: { [key: string]: { value: number; change: number; trend: string } };
    news_summary: string;
    potential_stocks: PotentialStock[];
    market_sentiment: {
      technical?: {
        rsi: number;
        macd_signal: string;
        trend: string;
        volatility: number;
        volume_trend: string;
      };
      news?: {
        overall: string;
        score: number;
      };
    };
    analysis_report: string;
  } | null;
  loading: boolean;
}

const MarketAnalysis: React.FC<MarketAnalysisProps> = ({ onAnalyze, result, loading }) => {
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    try {
      setError(null);
      await onAnalyze();
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析过程中出错');
    }
  };

  return (
    <div className="p-4">
      <div className="mb-4">
        <h2 className="text-2xl font-bold mb-4">市场分析</h2>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          {loading ? '分析中...' : '开始分析'}
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* 市场概览 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">市场指数概览</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(result.market_overview).map(([name, data]) => (
                <div key={name} className="border p-4 rounded">
                  <h4 className="font-medium">{name}</h4>
                  <p className={`text-lg ${data.daily_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {data.daily_change.toFixed(2)}%
                  </p>
                  <p className="text-sm text-gray-600">
                    月度变化: {data.monthly_change.toFixed(2)}%
                  </p>
                  <p className="text-sm text-gray-600">
                    波动率: {data.volatility.toFixed(2)}%
                  </p>
                  <p className="text-sm text-gray-600">
                    RSI: {data.rsi.toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* 宏观经济指标 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">宏观经济指标</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(result.macro_indicators).map(([name, data]) => (
                <div key={name} className="border p-4 rounded">
                  <h4 className="font-medium">{name}</h4>
                  <p className={`text-lg ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {data.value.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600">
                    变化: {data.change.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600">
                    趋势: {data.trend}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* 热门行业板块 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">热门行业板块</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(result.hot_sectors).map(([name, data]) => (
                <div key={name} className="border p-4 rounded">
                  <h4 className="font-medium">{name}</h4>
                  <p className={`${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    涨跌幅: {data.change.toFixed(2)}%
                  </p>
                  <p className="text-sm text-gray-600">
                    成交量变化: {data.volume_change.toFixed(2)}%
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* 市场情绪 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">市场情绪</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.market_sentiment.technical && (
                <div className="border p-4 rounded">
                  <h4 className="font-medium">技术面情绪</h4>
                  <p>RSI: {result.market_sentiment.technical.rsi.toFixed(2)}</p>
                  <p>MACD信号: {result.market_sentiment.technical.macd_signal}</p>
                  <p>趋势: {result.market_sentiment.technical.trend}</p>
                  <p>成交量趋势: {result.market_sentiment.technical.volume_trend}</p>
                </div>
              )}
              {result.market_sentiment.news && (
                <div className="border p-4 rounded">
                  <h4 className="font-medium">新闻情绪</h4>
                  <p>整体情绪: {result.market_sentiment.news.overall}</p>
                  <p>情绪得分: {result.market_sentiment.news.score.toFixed(2)}</p>
                </div>
              )}
            </div>
          </div>

          {/* 市场新闻分析 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">市场新闻分析</h3>
            <div className="whitespace-pre-line">{result.news_summary}</div>
          </div>

          {/* 潜力股票 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">潜力股票</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-4 py-2">股票</th>
                    <th className="px-4 py-2">行业</th>
                    <th className="px-4 py-2">动量</th>
                    <th className="px-4 py-2">RSI</th>
                    <th className="px-4 py-2">市盈率</th>
                    <th className="px-4 py-2">利润率</th>
                    <th className="px-4 py-2">总评分</th>
                  </tr>
                </thead>
                <tbody>
                  {result.potential_stocks.map((stock) => (
                    <tr key={stock.symbol} className="border-b">
                      <td className="px-4 py-2">
                        <div>{stock.symbol}</div>
                        <div className="text-sm text-gray-600">{stock.name}</div>
                      </td>
                      <td className="px-4 py-2">{stock.sector}</td>
                      <td className={`px-4 py-2 ${stock.momentum_indicators.price_momentum >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {stock.momentum_indicators.price_momentum.toFixed(2)}%
                      </td>
                      <td className="px-4 py-2">{stock.technical_indicators.rsi.toFixed(2)}</td>
                      <td className="px-4 py-2">{stock.fundamental_indicators.pe_ratio.toFixed(2)}</td>
                      <td className="px-4 py-2">{stock.fundamental_indicators.profit_margin.toFixed(2)}%</td>
                      <td className="px-4 py-2">{stock.total_score.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 分析报告 */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">市场分析报告</h3>
            <div className="whitespace-pre-line">{result.analysis_report}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketAnalysis; 
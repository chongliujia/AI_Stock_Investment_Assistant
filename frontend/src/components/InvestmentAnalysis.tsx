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

interface AnalysisResult {
  stockAnalysis: {
    type: string;
    title: string;
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      borderColor?: string;
      backgroundColor?: string;
    }>;
  };
  investmentAdvice: {
    advice: string;
    fundamentals: {
      [key: string]: {
        name: string;
        sector: string;
        marketCap: number;
        pe: number;
        forwardPE: number;
        profitMargin: number;
        dividendYield: number;
        beta: number;
      };
    };
    charts: Array<{
      type: string;
      title: string;
      labels: string[];
      datasets: Array<{
        label: string;
        data: number[];
        borderColor?: string;
        backgroundColor?: string;
      }>;
    }>;
  };
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
    </div>
  );
}

function InvestmentAnalysis() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  // 从本地存储加载最近搜索记录
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  // 保存搜索记录到本地存储
  const saveSearch = useCallback((search: string) => {
    const updated = [search, ...recentSearches.filter(s => s !== search)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));
  }, [recentSearches]);

  const handleAnalysis = async () => {
    if (!query.trim()) {
      setError('请输入股票代码或公司名称');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);  // 清除之前的结果

    try {
      console.log('Sending request for:', query.trim());
      const response = await fetch('/api/analyze-investment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() }),
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);

      if (!response.ok) {
        throw new Error(data.detail || '分析请求失败');
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
    }
  };

  // 添加键盘快捷键支持
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        handleAnalysis();
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [query]);

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4 text-gray-800">智能投资分析</h1>
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="输入股票代码或公司名称（例如：AAPL 或 Apple）"
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                disabled={loading}
              />
              {recentSearches.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {recentSearches.map((search, index) => (
                    <button
                      key={index}
                      onClick={() => setQuery(search)}
                      className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                    >
                      {search}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={handleAnalysis}
              disabled={loading}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <LoadingSpinner />
                  <span>分析中...</span>
                </>
              ) : (
                <>
                  <span>开始分析</span>
                  <span className="text-sm opacity-75">(Enter)</span>
                </>
              )}
            </button>
          </div>
          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span>{error}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {result && (
        <div className="space-y-8 animate-fade-in">
          {/* 投资建议部分 */}
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">投资建议</h2>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-gray-700">
                {result.investmentAdvice.advice}
              </pre>
            </div>
          </div>

          {/* 基本面数据表格 */}
          <div className="overflow-x-auto bg-white rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold p-6 text-gray-800">基本面数据</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="p-4 text-left text-gray-600">股票</th>
                    <th className="p-4 text-left text-gray-600">行业</th>
                    <th className="p-4 text-left text-gray-600">市值(B$)</th>
                    <th className="p-4 text-left text-gray-600">市盈率</th>
                    <th className="p-4 text-left text-gray-600">预期市盈率</th>
                    <th className="p-4 text-left text-gray-600">利润率(%)</th>
                    <th className="p-4 text-left text-gray-600">股息率(%)</th>
                    <th className="p-4 text-left text-gray-600">Beta系数</th>
                  </tr>
                </thead>
                <tbody>
                  {result.investmentAdvice?.fundamentals && 
                   Object.entries(result.investmentAdvice.fundamentals).map(([symbol, fund]) => (
                    <tr key={symbol} className="border-t hover:bg-gray-50">
                      <td className="p-4 font-medium">{symbol} ({fund.name})</td>
                      <td className="p-4">{fund.sector}</td>
                      <td className="p-4">{fund.marketCap.toFixed(2)}</td>
                      <td className="p-4">{fund.pe.toFixed(2)}</td>
                      <td className="p-4">{fund.forwardPE.toFixed(2)}</td>
                      <td className="p-4">{fund.profitMargin.toFixed(2)}</td>
                      <td className="p-4">{fund.dividendYield.toFixed(2)}</td>
                      <td className="p-4">{fund.beta.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 图表展示 */}
          <div className="grid gap-8">
            {result.investmentAdvice?.charts?.map((chart, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-lg">
                <h3 className="text-xl font-bold mb-4 text-gray-800">{chart.title}</h3>
                {chart.type === 'line' ? (
                  <Line
                    data={{
                      labels: chart.labels,
                      datasets: chart.datasets.map(dataset => ({
                        ...dataset,
                        borderColor: dataset.borderColor || '#3B82F6',
                        backgroundColor: dataset.backgroundColor || 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                      }))
                    }}
                    options={{
                      responsive: true,
                      plugins: {
                        legend: { position: 'top' },
                        title: { display: false }
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
                ) : (
                  <Bar
                    data={{
                      labels: chart.labels,
                      datasets: chart.datasets.map(dataset => ({
                        ...dataset,
                        backgroundColor: dataset.backgroundColor || 'rgba(59, 130, 246, 0.6)'
                      }))
                    }}
                    options={{
                      responsive: true,
                      plugins: {
                        legend: { position: 'top' },
                        title: { display: false }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
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
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default InvestmentAnalysis; 
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
      [key: string]: {
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
        analysis: string;
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

interface InvestmentAnalysisProps {
  initialQuery?: string;
}

// 添加类型定义
interface ChartDataset {
  label: string;
  data: number[];
  borderColor?: string;
  backgroundColor?: string;
}

interface ChartData {
  type: string;
  title: string;
  labels: string[];
  datasets: ChartDataset[];
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
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
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
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
      const symbols = query.trim().split(/[,，\s]+/).filter(Boolean);
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

  // 优化图表渲染
  const renderChart = useCallback((chart: ChartData, index: number) => {
    const commonOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' as const },
        title: { display: false }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: { color: 'rgba(0, 0, 0, 0.05)' }
        },
        x: {
          grid: { display: false }
        }
      }
    };

    return (
      <div key={index} className="chart-container h-[400px]">
        <h3 className="text-xl font-bold mb-4 text-gray-800">{chart.title}</h3>
        {chart.type === 'line' ? (
          <Line
            data={{
              labels: chart.labels,
              datasets: chart.datasets.map((dataset: ChartDataset) => ({
                ...dataset,
                borderColor: dataset.borderColor || '#3B82F6',
                backgroundColor: dataset.backgroundColor || 'rgba(59, 130, 246, 0.1)',
                tension: 0.1
              }))
            }}
            options={commonOptions}
          />
        ) : (
          <Bar
            data={{
              labels: chart.labels,
              datasets: chart.datasets.map((dataset: ChartDataset) => ({
                ...dataset,
                backgroundColor: dataset.backgroundColor || 'rgba(59, 130, 246, 0.6)'
              }))
            }}
            options={commonOptions}
          />
        )}
      </div>
    );
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="输入股票代码或公司名称（例如：AAPL 或 Apple）"
              className="input"
              disabled={loading}
            />
            {recentSearches.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {recentSearches.map((search, index) => (
                  <button
                    key={index}
                    onClick={() => setQuery(search)}
                    className="btn btn-secondary text-sm"
                  >
                    {search}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={handleAnalysis}
            disabled={loading || !query.trim()}
            className="btn btn-primary min-w-[120px] flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>分析中...</span>
              </>
            ) : (
              <>
                <span>开始分析</span>
                <span className="text-xs opacity-75">(Enter)</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 animate-slide-in">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}
      </div>

      {result && (
        <div className="space-y-6 animate-fade-in">
          <div className="card">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">投资建议</h2>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-gray-700 bg-gray-50 rounded-lg p-4">
                {result.investmentAdvice.advice}
              </pre>
            </div>
          </div>

          {/* 公司信息 */}
          {result.investmentAdvice?.companyInfo && 
            Object.entries(result.investmentAdvice.companyInfo).map(([symbol, info]) => (
              <div key={symbol} className="card">
                <h2 className="text-2xl font-bold mb-4 text-gray-800">{info.name} ({symbol})</h2>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold mb-2">公司介绍</h3>
                    <p className="text-gray-700">{info.introduction}</p>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-2">主营业务</h3>
                    <ul className="list-disc list-inside space-y-1">
                      {info.mainBusinesses.map((business, index) => (
                        <li key={index} className="text-gray-700">{business}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <h4 className="font-medium text-gray-600">行业</h4>
                      <p>{info.industry}</p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-600">板块</h4>
                      <p>{info.sector}</p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-600">国家/地区</h4>
                      <p>{info.country || '未知'}</p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-600">员工人数</h4>
                      <p>{info.employees.toLocaleString() || '未知'}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          }

          <div className="table-container">
            <h2 className="text-2xl font-bold p-6 text-gray-800">基本面数据</h2>
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>股票</th>
                    <th>行业</th>
                    <th>市值(B$)</th>
                    <th>市盈率</th>
                    <th>预期市盈率</th>
                    <th>利润率(%)</th>
                    <th>股息率(%)</th>
                    <th>Beta系数</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {result.investmentAdvice?.fundamentals && 
                   Object.entries(result.investmentAdvice.fundamentals).map(([symbol, fund]) => (
                    <tr key={symbol} className="hover:bg-gray-50 transition-colors">
                      <td>
                        <div className="font-medium">{symbol}</div>
                        <div className="text-sm text-gray-500">{result.investmentAdvice.companyInfo[symbol]?.name || symbol}</div>
                      </td>
                      <td>{result.investmentAdvice.companyInfo[symbol]?.sector || 'Unknown'}</td>
                      <td>{fund.valuation_metrics.market_cap.toFixed(2)}</td>
                      <td>{fund.valuation_metrics.pe_ratio.toFixed(2)}</td>
                      <td>{fund.valuation_metrics.forward_pe.toFixed(2)}</td>
                      <td>{fund.profitability_metrics.profit_margin.toFixed(2)}</td>
                      <td>{fund.profitability_metrics.dividend_yield.toFixed(2)}</td>
                      <td>{fund.risk_metrics.beta.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="responsive-grid">
            {result.investmentAdvice?.charts?.map(renderChart)}
          </div>
        </div>
      )}
    </div>
  );
}

export default InvestmentAnalysis; 
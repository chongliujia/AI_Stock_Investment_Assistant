import React, { useState } from 'react';
import InvestmentAnalysis from './components/InvestmentAnalysis';
import MarketAnalysis from './components/MarketAnalysis';
import { useTheme } from './hooks/useTheme';

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

interface MarketResult {
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
}

function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'investment' | 'market'>('home');
  const [marketResult, setMarketResult] = useState<MarketResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const { theme } = useTheme();

  const handleMarketAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_type: 'analyze_market',
          kwargs: {}
        }),
      });

      if (!response.ok) {
        throw new Error('市场分析请求失败');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法读取响应流');
      }

      let partialResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = new TextDecoder().decode(value);
        console.log('Received chunk:', chunk);
        partialResponse += chunk;

        try {
          const data = JSON.parse(partialResponse);
          console.log('Parsed data:', data);
          if (data.status === 'success') {
            setMarketResult((prevResult: MarketResult | null) => {
              console.log('Previous result:', prevResult);
              console.log('New data:', data.data);
              const newResult = {
                ...prevResult,
                ...data.data
              };
              console.log('Updated result:', newResult);
              return newResult;
            });
          }
          partialResponse = '';
        } catch (e) {
          console.log('JSON parse error (expected for partial chunks):', e);
          continue;
        }
      }
    } catch (error) {
      console.error('Market analysis error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setActiveTab('investment');
  };

  const renderHome = () => (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-4xl w-full px-4">
        <h1 className={`text-4xl md:text-5xl font-bold text-center mb-8 
          ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
          智能投资助手
        </h1>
        <div className="flex flex-col items-center space-y-8">
          {/* 搜索框 */}
          <div className="w-full max-w-2xl">
            <div className="relative">
              <input
                type="text"
                placeholder="输入股票代码或公司名称..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch(searchQuery)}
                className={`w-full px-4 py-3 rounded-lg shadow-sm text-lg 
                  ${theme === 'dark' 
                    ? 'bg-gray-800 text-white border-gray-700 focus:border-blue-500' 
                    : 'bg-white text-gray-900 border-gray-300 focus:border-blue-500'
                  } border focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50`}
              />
              <button
                onClick={() => handleSearch(searchQuery)}
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-1.5 rounded-md
                  ${theme === 'dark'
                    ? 'bg-blue-600 hover:bg-blue-700'
                    : 'bg-blue-500 hover:bg-blue-600'
                  } text-white transition-colors duration-200`}
              >
                搜索
              </button>
            </div>
          </div>

          {/* 功能按钮 */}
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => setActiveTab('market')}
              className={`px-6 py-3 rounded-lg shadow-sm text-lg transition-colors duration-200
                ${theme === 'dark'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
            >
              市场分析
            </button>
            <button
              onClick={() => setActiveTab('investment')}
              className={`px-6 py-3 rounded-lg shadow-sm text-lg transition-colors duration-200
                ${theme === 'dark'
                  ? 'bg-gray-700 hover:bg-gray-600 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
                }`}
            >
              个股分析
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {activeTab === 'home' ? (
        renderHome()
      ) : (
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-7xl mx-auto">
            <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden`}>
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="flex -mb-px" aria-label="Tabs">
                  <button
                    onClick={() => setActiveTab('home')}
                    className={`${
                      theme === 'dark' ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
                    } px-4 py-2 font-medium text-sm`}
                  >
                    返回首页
                  </button>
                  <button
                    onClick={() => setActiveTab('investment')}
                    className={`${
                      activeTab === 'investment'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-4 px-8 border-b-2 font-medium text-sm transition-colors duration-200`}
                  >
                    个股分析
                  </button>
                  <button
                    onClick={() => setActiveTab('market')}
                    className={`${
                      activeTab === 'market'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-4 px-8 border-b-2 font-medium text-sm transition-colors duration-200`}
                  >
                    市场分析
                  </button>
                </nav>
              </div>

              <div className="p-6">
                <div className={`transition-opacity duration-200 ${loading ? 'opacity-50' : 'opacity-100'}`}>
                  {activeTab === 'investment' ? (
                    <InvestmentAnalysis initialQuery={searchQuery} />
                  ) : (
                    <MarketAnalysis
                      onAnalyze={handleMarketAnalysis}
                      result={marketResult}
                      loading={loading}
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      )}

      <footer className={`mt-auto py-4 ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className={`text-center text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
            © 2024 智能投资助手. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
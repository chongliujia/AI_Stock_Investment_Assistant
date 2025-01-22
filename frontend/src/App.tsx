import React, { useState } from 'react';
import InvestmentAnalysis from './components/InvestmentAnalysis';
import MarketAnalysis from './components/MarketAnalysis';

function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'investment' | 'market'>('home');
  const [marketResult, setMarketResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

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

      const data = await response.json();
      if (data.status === 'success') {
        setMarketResult(data.data);
        setActiveTab('market');
      } else {
        throw new Error(data.error || '分析过程中出错');
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

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <button 
                  onClick={() => {
                    setActiveTab('home');
                    setSearchQuery('');
                  }}
                  className="text-2xl font-bold text-blue-600 hover:text-blue-700 transition-colors"
                >
                  智能投资助手
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'home' ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] animate-fade-in">
            <h1 className="text-4xl font-bold text-gray-900 mb-8">智能投资分析</h1>
            <div className="w-full max-w-2xl space-y-6">
              <div className="card p-8">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="输入股票代码或公司名称（例如：AAPL 或 Apple）"
                  className="input text-lg mb-4"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && searchQuery.trim()) {
                      handleSearch(searchQuery);
                    }
                  }}
                />
                <div className="flex justify-center gap-4 mt-6">
                  <button
                    onClick={() => handleSearch(searchQuery)}
                    disabled={!searchQuery.trim()}
                    className="btn btn-primary px-8 py-3"
                  >
                    分析股票
                  </button>
                  <button
                    onClick={() => {
                      handleMarketAnalysis();
                      setActiveTab('market');
                    }}
                    className="btn btn-secondary px-8 py-3"
                  >
                    市场分析
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px" aria-label="Tabs">
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
        )}
      </main>

      <footer className="bg-white mt-auto">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            © 2024 智能投资助手. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App; 
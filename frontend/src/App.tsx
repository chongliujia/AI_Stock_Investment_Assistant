import React, { useState } from 'react';
import InvestmentAnalysis from './components/InvestmentAnalysis';
import MarketAnalysis from './components/MarketAnalysis';

function App() {
  const [activeTab, setActiveTab] = useState<'investment' | 'market'>('investment');
  const [marketResult, setMarketResult] = useState(null);
  const [loading, setLoading] = useState(false);

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

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">智能投资助手</h1>
      
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('investment')}
              className={`mr-8 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'investment'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              个股分析
            </button>
            <button
              onClick={() => setActiveTab('market')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'market'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              市场分析
            </button>
          </nav>
        </div>
      </div>

      <div className="mt-6">
        {activeTab === 'investment' ? (
          <InvestmentAnalysis />
        ) : (
          <MarketAnalysis
            onAnalyze={handleMarketAnalysis}
            result={marketResult}
            loading={loading}
          />
        )}
      </div>
    </div>
  );
}

export default App; 
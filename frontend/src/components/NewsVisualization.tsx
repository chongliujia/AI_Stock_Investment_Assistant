import React from 'react';

interface NewsItem {
  title: string;
  publisher: string;
  link: string;
  published: string;
}

interface NewsData {
  symbol: string;
  news: NewsItem[];
}

interface SentimentAnalysis {
  symbol: string;
  analysis: string;
}

interface NewsVisualizationProps {
  newsData: NewsData[];
  sentimentAnalysis: SentimentAnalysis[];
}

function NewsVisualization({ newsData, sentimentAnalysis }: NewsVisualizationProps) {
  return (
    <div style={{ padding: '20px' }}>
      {newsData.map((stockNews, index) => (
        <div key={stockNews.symbol} style={{ marginBottom: '30px' }}>
          <h3 style={{ color: '#2E7D32', marginBottom: '15px' }}>
            {stockNews.symbol} 相关新闻
          </h3>
          
          {/* 情绪分析 */}
          <div style={{
            padding: '15px',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px',
            marginBottom: '15px'
          }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#1976D2' }}>市场情绪分析</h4>
            <p style={{ margin: 0, whiteSpace: 'pre-line' }}>
              {sentimentAnalysis[index]?.analysis || '暂无分析'}
            </p>
          </div>

          {/* 新闻列表 */}
          <div style={{ display: 'grid', gap: '15px' }}>
            {stockNews.news.map((item, i) => (
              <div key={i} style={{
                padding: '15px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                backgroundColor: 'white'
              }}>
                <h4 style={{ margin: '0 0 10px 0' }}>
                  <a href={item.link}
                     target="_blank"
                     rel="noopener noreferrer"
                     style={{ color: '#1976D2', textDecoration: 'none' }}>
                    {item.title}
                  </a>
                </h4>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  color: '#666',
                  fontSize: '0.9em'
                }}>
                  <span>{item.publisher}</span>
                  <span>{item.published}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default NewsVisualization; 
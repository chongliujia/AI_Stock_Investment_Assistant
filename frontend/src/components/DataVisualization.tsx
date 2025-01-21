import React from 'react';
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
  ChartData,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import NewsVisualization from './NewsVisualization';

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

interface DataVisualizationProps {
  data: {
    type: string;
    title?: string;
    labels?: string[];
    datasets?: any[];
    charts?: any[];
    metrics?: any[];
    newsData?: any[];
    sentimentAnalysis?: any[];
  };
}

function DataVisualization({ data }: DataVisualizationProps) {
  if (data.type === 'news') {
    return (
      <NewsVisualization 
        newsData={data.newsData} 
        sentimentAnalysis={data.sentimentAnalysis} 
      />
    );
  }

  if (data.type === 'fundamental') {
    return (
      <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
        {/* 指标概览表格 */}
        <div style={{ marginBottom: '20px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={tableHeaderStyle}>股票</th>
                <th style={tableHeaderStyle}>市值(B$)</th>
                <th style={tableHeaderStyle}>市盈率</th>
                <th style={tableHeaderStyle}>利润率(%)</th>
              </tr>
            </thead>
            <tbody>
              {data.metrics?.map((metric, index) => (
                <tr key={metric.symbol}>
                  <td style={tableCellStyle}>{metric.symbol}</td>
                  <td style={tableCellStyle}>{metric.marketCap}</td>
                  <td style={tableCellStyle}>{metric.pe}</td>
                  <td style={tableCellStyle}>{metric.profitMargin}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* 图表展示 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
          {data.charts?.map((chart, index) => (
            <div key={index}>
              <Bar
                data={{
                  labels: chart.labels,
                  datasets: chart.datasets,
                }}
                options={{
                  responsive: true,
                  plugins: {
                    legend: { position: 'top' },
                    title: {
                      display: true,
                      text: chart.title,
                    },
                  },
                }}
              />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 原有的图表渲染逻辑
  const chartData: ChartData<'line' | 'bar'> = {
    labels: data.labels,
    datasets: data.datasets?.map(dataset => ({
      ...dataset,
      borderColor: dataset.borderColor || '#4CAF50',
      backgroundColor: dataset.backgroundColor || 'rgba(76, 175, 80, 0.2)',
    })),
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: data.title,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
      {data.type === 'line' ? (
        <Line data={chartData} options={options} />
      ) : (
        <Bar data={chartData} options={options} />
      )}
    </div>
  );
}

const tableHeaderStyle = {
  padding: '12px',
  backgroundColor: '#f5f5f5',
  borderBottom: '2px solid #ddd',
  textAlign: 'left' as const,
};

const tableCellStyle = {
  padding: '8px',
  borderBottom: '1px solid #ddd',
};

export default DataVisualization; 
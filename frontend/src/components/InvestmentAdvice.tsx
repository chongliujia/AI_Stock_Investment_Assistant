import React from 'react';
import { Line, Bar } from 'react-chartjs-2';

interface Fundamental {
  name: string;
  sector: string;
  marketCap: number;
  pe: number;
  forwardPE: number;
  profitMargin: number;
  dividendYield: number;
  beta: number;
}

interface ChartData {
  type: string;
  title: string;
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
  }>;
}

interface InvestmentAdviceProps {
  data: {
    advice: string;
    fundamentals: { [key: string]: Fundamental };
    charts: ChartData[];
  };
}

function InvestmentAdvice({ data }: InvestmentAdviceProps) {
  return (
    <div style={{ padding: '20px' }}>
      {/* 投资建议部分 */}
      <div style={{
        backgroundColor: '#f8f9fa',
        padding: '20px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ marginTop: 0, color: '#2E7D32' }}>投资建议</h3>
        <pre style={{
          whiteSpace: 'pre-wrap',
          fontFamily: 'inherit',
          margin: 0
        }}>
          {data.advice}
        </pre>
      </div>

      {/* 基本面数据表格 */}
      <div style={{ marginBottom: '30px', overflowX: 'auto' }}>
        <h3 style={{ color: '#2E7D32' }}>基本面数据</h3>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          backgroundColor: 'white',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={tableHeaderStyle}>股票</th>
              <th style={tableHeaderStyle}>行业</th>
              <th style={tableHeaderStyle}>市值(B$)</th>
              <th style={tableHeaderStyle}>市盈率</th>
              <th style={tableHeaderStyle}>预期市盈率</th>
              <th style={tableHeaderStyle}>利润率(%)</th>
              <th style={tableHeaderStyle}>股息率(%)</th>
              <th style={tableHeaderStyle}>Beta系数</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.fundamentals).map(([symbol, fund]) => (
              <tr key={symbol}>
                <td style={tableCellStyle}>{symbol} ({fund.name})</td>
                <td style={tableCellStyle}>{fund.sector}</td>
                <td style={tableCellStyle}>{fund.marketCap.toFixed(2)}</td>
                <td style={tableCellStyle}>{fund.pe.toFixed(2)}</td>
                <td style={tableCellStyle}>{fund.forwardPE.toFixed(2)}</td>
                <td style={tableCellStyle}>{fund.profitMargin.toFixed(2)}</td>
                <td style={tableCellStyle}>{fund.dividendYield.toFixed(2)}</td>
                <td style={tableCellStyle}>{fund.beta.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 图表展示 */}
      <div style={{ display: 'grid', gap: '20px' }}>
        {data.charts.map((chart, index) => (
          <div key={index} style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            {chart.type === 'line' ? (
              <Line
                data={{
                  labels: chart.labels,
                  datasets: chart.datasets.map(dataset => ({
                    ...dataset,
                    borderColor: dataset.borderColor || '#4CAF50',
                    backgroundColor: dataset.backgroundColor || 'rgba(76, 175, 80, 0.1)'
                  }))
                }}
                options={{
                  responsive: true,
                  plugins: {
                    legend: { position: 'top' },
                    title: {
                      display: true,
                      text: chart.title
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
                    backgroundColor: dataset.backgroundColor || 'rgba(76, 175, 80, 0.6)'
                  }))
                }}
                options={{
                  responsive: true,
                  plugins: {
                    legend: { position: 'top' },
                    title: {
                      display: true,
                      text: chart.title
                    }
                  }
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

const tableHeaderStyle = {
  padding: '12px',
  textAlign: 'left' as const,
  borderBottom: '2px solid #ddd'
};

const tableCellStyle = {
  padding: '12px',
  borderBottom: '1px solid #ddd'
};

export default InvestmentAdvice; 
import React from 'react';
import { Handle, Position } from 'reactflow';
import DataVisualization from './DataVisualization';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import InvestmentAdvice from './InvestmentAdvice';

interface NodeData {
  type: string;
  label: string;
  error?: string;
  loading?: boolean;
  onRetry?: () => void;
  analysisResult?: any;
  prompt?: string;
}

function CustomNode({ data }: { data: NodeData }) {
  return (
    <div style={{ 
      padding: '15px',
      border: `2px solid ${data.error ? '#ef5350' : '#4CAF50'}`,
      borderRadius: '8px',
      backgroundColor: 'white',
      minWidth: '150px',
      maxWidth: data.type === 'dataAnalyzer' || data.type === 'stockAnalyzer' || data.type === 'investmentAdvisor' ? '800px' : '150px',
      boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
    }}>
      <Handle 
        type="target" 
        position={Position.Top} 
        style={{ background: data.error ? '#ef5350' : '#4CAF50' }}
      />
      <div style={{
        fontWeight: 'bold',
        marginBottom: '8px',
        color: data.error ? '#c62828' : '#2E7D32',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>{data.label}</span>
        {data.loading && <LoadingSpinner size="small" />}
      </div>

      {data.error ? (
        <ErrorMessage 
          message={data.error} 
          onRetry={data.onRetry}
        />
      ) : (
        <>
          {(data.type === 'dataAnalyzer' || data.type === 'stockAnalyzer') && 
           data.analysisResult && !data.loading && (
            <DataVisualization data={data.analysisResult} />
          )}
          {data.type === 'investmentAdvisor' && 
           data.analysisResult && !data.loading && (
            <InvestmentAdvice data={JSON.parse(data.analysisResult)} />
          )}
          {data.prompt && (
            <div style={{
              fontSize: '12px',
              color: '#666',
              marginTop: '4px',
              wordBreak: 'break-word'
            }}>
              {data.prompt.substring(0, 50)}...
            </div>
          )}
        </>
      )}
      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        style={{ background: data.error ? '#ef5350' : '#4CAF50' }}
      />
    </div>
  );
}

export default CustomNode; 
import React from 'react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div style={{
      padding: '20px',
      backgroundColor: '#ffebee',
      border: '1px solid #ffcdd2',
      borderRadius: '8px',
      color: '#c62828',
      margin: '10px 0'
    }}>
      <div style={{ marginBottom: onRetry ? '10px' : 0 }}>
        <strong>错误：</strong> {message}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            backgroundColor: '#ef5350',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          重试
        </button>
      )}
    </div>
  );
}

export default ErrorMessage; 
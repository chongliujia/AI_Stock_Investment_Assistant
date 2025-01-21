import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
}

function LoadingSpinner({ size = 'medium', message = '加载中...' }: LoadingSpinnerProps) {
  const spinnerSize = {
    small: '20px',
    medium: '40px',
    large: '60px'
  }[size];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        width: spinnerSize,
        height: spinnerSize,
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #4CAF50',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        marginBottom: '10px'
      }} />
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
      {message && <div style={{ color: '#666' }}>{message}</div>}
    </div>
  );
}

export default LoadingSpinner; 
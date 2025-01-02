import React from 'react';

interface WorkflowToolbarProps {
  onExecute: () => void;
  isExecuting: boolean;
}

function WorkflowToolbar({ onExecute, isExecuting }: WorkflowToolbarProps) {
  return (
    <div style={{
      padding: '10px',
      borderBottom: '1px solid #ccc',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}>
      <div>
        <button
          onClick={onExecute}
          disabled={isExecuting}
          style={{
            padding: '8px 16px',
            backgroundColor: isExecuting ? '#ccc' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isExecuting ? 'not-allowed' : 'pointer',
          }}
        >
          {isExecuting ? '执行中...' : '执行工作流'}
        </button>
      </div>
      <div>
        <button style={{ marginRight: '10px' }}>保存工作流</button>
        <button>加载工作流</button>
      </div>
    </div>
  );
}

export default WorkflowToolbar; 
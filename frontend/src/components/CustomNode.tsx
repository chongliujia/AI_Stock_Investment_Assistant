import React from 'react';
import { Handle, Position } from 'reactflow';

function CustomNode({ data }) {
  return (
    <div style={{ 
      padding: '15px',
      border: '2px solid #4CAF50',
      borderRadius: '8px',
      backgroundColor: 'white',
      minWidth: '150px',
      boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
    }}>
      <Handle 
        type="target" 
        position={Position.Top} 
        style={{ background: '#4CAF50' }}
      />
      <div style={{
        fontWeight: 'bold',
        marginBottom: '8px',
        color: '#2E7D32'
      }}>
        {data.label}
      </div>
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
      <Handle 
        type="source" 
        position={Position.Bottom} 
        style={{ background: '#4CAF50' }}
      />
    </div>
  );
}

export default CustomNode; 
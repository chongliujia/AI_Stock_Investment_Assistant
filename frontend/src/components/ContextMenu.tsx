import React from 'react';

interface ContextMenuProps {
  x: number;
  y: number;
  onDelete: () => void;
  onClose: () => void;
}

function ContextMenu({ x, y, onDelete, onClose }: ContextMenuProps) {
  return (
    <div
      style={{
        position: 'fixed',
        left: x,
        top: y,
        background: 'white',
        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
        borderRadius: '4px',
        padding: '4px 0',
        zIndex: 1000,
      }}
      onMouseLeave={onClose}
    >
      <div
        onClick={() => {
          onDelete();
          onClose();
        }}
        style={{
          padding: '8px 16px',
          cursor: 'pointer',
          fontSize: '14px',
          color: '#dc3545',
          ':hover': {
            backgroundColor: '#f8f9fa'
          }
        }}
      >
        删除节点
      </div>
    </div>
  );
}

export default ContextMenu; 
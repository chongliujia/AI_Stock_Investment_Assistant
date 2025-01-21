import React, { useState, useEffect } from 'react';

function NodeConfigPanel({ node, onClose, onUpdate, onDelete }) {
  const [models, setModels] = useState({});

  useEffect(() => {
    // 获取可用模型列表
    fetch('/api/models')
      .then(res => res.json())
      .then(data => setModels(data.models));
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    onUpdate(data);
  };

  return (
    <div style={{ width: '300px', padding: '20px', borderLeft: '1px solid #ccc' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0 }}>节点配置</h3>
        <button
          onClick={onDelete}
          style={{
            padding: '4px 8px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          删除节点
        </button>
      </div>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label>AI模型：</label>
          <select 
            name="model" 
            defaultValue={node.data.model || 'gpt-4o'}
            style={{
              width: '100%',
              padding: '8px',
              marginTop: '5px',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          >
            {Object.entries(models).map(([key, name]) => (
              <option key={key} value={key}>{name}</option>
            ))}
          </select>
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label>提示词：</label>
          <textarea
            name="prompt"
            defaultValue={node.data.prompt || ''}
            style={{ 
              width: '100%', 
              height: '100px',
              marginTop: '5px',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label>文档类型：</label>
          <select 
            name="docType" 
            defaultValue={node.data.docType || '报告'}
            style={{
              width: '100%',
              padding: '8px',
              marginTop: '5px',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          >
            <option value="报告">报告</option>
            <option value="分析">分析</option>
            <option value="总结">总结</option>
          </select>
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label>字数：</label>
          <input
            type="number"
            name="wordCount"
            defaultValue={node.data.wordCount || 1000}
            style={{
              width: '100%',
              padding: '8px',
              marginTop: '5px',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          />
        </div>
        <div style={{ marginBottom: '20px' }}>
          <label>语言：</label>
          <select 
            name="language" 
            defaultValue={node.data.language || 'zh'}
            style={{
              width: '100%',
              padding: '8px',
              marginTop: '5px',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          >
            <option value="zh">中文</option>
            <option value="en">英文</option>
          </select>
        </div>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button 
            type="submit"
            style={{
              padding: '8px 16px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            保存
          </button>
          <button 
            type="button" 
            onClick={onClose}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            关闭
          </button>
        </div>
      </form>
    </div>
  );
}

export default NodeConfigPanel; 
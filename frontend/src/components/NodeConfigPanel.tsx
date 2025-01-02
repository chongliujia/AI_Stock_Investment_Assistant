import React from 'react';

function NodeConfigPanel({ node, onClose, onUpdate }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    onUpdate(data);
  };

  return (
    <div style={{ width: '300px', padding: '20px', borderLeft: '1px solid #ccc' }}>
      <h3>节点配置</h3>
      <form onSubmit={handleSubmit}>
        <div>
          <label>提示词：</label>
          <textarea
            name="prompt"
            defaultValue={node.data.prompt || ''}
            style={{ width: '100%', height: '100px' }}
          />
        </div>
        <div>
          <label>文档类型：</label>
          <select name="docType" defaultValue={node.data.docType || '报告'}>
            <option value="报告">报告</option>
            <option value="分析">分析</option>
            <option value="总结">总结</option>
          </select>
        </div>
        <div>
          <label>字数：</label>
          <input
            type="number"
            name="wordCount"
            defaultValue={node.data.wordCount || 1000}
          />
        </div>
        <div>
          <label>语言：</label>
          <select name="language" defaultValue={node.data.language || 'zh'}>
            <option value="zh">中文</option>
            <option value="en">英文</option>
          </select>
        </div>
        <button type="submit">保存</button>
        <button type="button" onClick={onClose}>关闭</button>
      </form>
    </div>
  );
}

export default NodeConfigPanel; 
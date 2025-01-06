import React from 'react';

interface NodeTemplate {
  type: string;
  label: string;
  description: string;
  category: string;
}

interface NodePaletteProps {
  templates: NodeTemplate[];
  style?: React.CSSProperties;
}

function NodePalette({ templates, style }: NodePaletteProps) {
  // 默认模板，确保至少有文档生成器可用
  const defaultTemplates = [
    {
      type: "documentGenerator",
      label: "文档生成器",
      description: "生成指定类型和长度的文档",
      category: "生成"
    }
  ];

  const allTemplates = templates.length ? templates : defaultTemplates;
  
  // 按类别分组模板
  const groupedTemplates = allTemplates.reduce((acc, template) => {
    const category = template.category || '其他';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(template);
    return acc;
  }, {});

  const handleDragStart = (event: React.DragEvent, template: NodeTemplate) => {
    event.dataTransfer.setData('application/reactflow', template.type);
    event.dataTransfer.effectAllowed = 'move';
    
    // 添加拖拽预览
    const dragPreview = document.createElement('div');
    dragPreview.innerHTML = template.label;
    dragPreview.className = 'node-drag-preview';
    document.body.appendChild(dragPreview);
    
    event.dataTransfer.setDragImage(dragPreview, 75, 25);
    setTimeout(() => document.body.removeChild(dragPreview), 0);
  };

  return (
    <div 
      className="node-palette"
      style={{ 
        padding: '20px', 
        borderRight: '1px solid #ccc', 
        backgroundColor: '#f5f5f5',
        overflowY: 'auto',
        height: '100%',
        ...style 
      }}
    >
      <h3 style={{ marginBottom: '20px', color: '#333' }}>智能体节点</h3>
      {Object.entries(groupedTemplates).map(([category, nodes]) => (
        <div key={category} className="node-category" style={{ marginBottom: '20px' }}>
          <h4 style={{ 
            color: '#666',
            borderBottom: '1px solid #ddd',
            paddingBottom: '8px',
            marginBottom: '12px'
          }}>{category}</h4>
          {nodes.map((template: NodeTemplate) => (
            <div
              key={template.type}
              className="draggable-node"
              draggable
              onDragStart={(e) => handleDragStart(e, template)}
              style={{
                border: '1px solid #ccc',
                padding: '12px',
                marginBottom: '10px',
                cursor: 'grab',
                borderRadius: '6px',
                backgroundColor: 'white',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                transition: 'all 0.2s ease',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                {template.label}
              </div>
              <div style={{ 
                fontSize: '12px', 
                color: '#666',
                lineHeight: '1.4'
              }}>
                {template.description}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export default NodePalette; 
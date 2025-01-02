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
  // 按类别分组模板
  const groupedTemplates = templates.reduce((acc, template) => {
    const category = template.category || '其他';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(template);
    return acc;
  }, {});

  return (
    <div style={{ padding: '20px', borderRight: '1px solid #ccc', ...style }}>
      <h3>智能体节点</h3>
      {Object.entries(groupedTemplates).map(([category, nodes]) => (
        <div key={category}>
          <h4>{category}</h4>
          {nodes.map((template: NodeTemplate) => (
            <div
              key={template.type}
              draggable
              onDragStart={(event) => {
                event.dataTransfer.setData('application/nodetype', template.type);
              }}
              style={{
                border: '1px solid #ccc',
                padding: '10px',
                marginBottom: '10px',
                cursor: 'grab',
                borderRadius: '4px',
              }}
            >
              <div style={{ fontWeight: 'bold' }}>{template.label}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
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
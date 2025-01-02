import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  Controls,
  Background,
  addEdge,
  Connection,
  Edge,
  Node,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import NodeConfigPanel from './components/NodeConfigPanel';
import CustomNode from './components/CustomNode';
import NodePalette from './components/NodePalette';
import WorkflowToolbar from './components/WorkflowToolbar';

const nodeTypes = {
  documentGenerator: CustomNode,
  researchAgent: CustomNode,
  dataAnalyzer: CustomNode,
};

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeTemplates, setNodeTemplates] = useState([]);
  const [isExecuting, setIsExecuting] = useState(false);

  // 获取节点模板
  useEffect(() => {
    fetch('/api/nodes/templates')
      .then(res => res.json())
      .then(data => setNodeTemplates(data.nodes));
  }, []);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((event: any, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const nodeType = event.dataTransfer.getData('application/nodetype');
      if (!nodeType) return;

      const template = nodeTemplates.find(t => t.type === nodeType);
      if (!template) return;

      const position = {
        x: event.clientX - 250,
        y: event.clientY - 100,
      };

      const newNode = {
        id: `${nodeType}-${Date.now()}`,
        type: nodeType,
        position,
        data: { 
          label: template.label,
          ...template.configFields.reduce((acc, field) => ({
            ...acc,
            [field.name]: field.type === 'select' ? field.options[0] : ''
          }), {})
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes, nodeTemplates]
  );

  const executeWorkflow = async () => {
    setIsExecuting(true);
    try {
      const response = await fetch('/api/workflow/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ nodes, edges }),
      });
      const result = await response.json();
      console.log('Workflow execution result:', result);
    } catch (error) {
      console.error('Error executing workflow:', error);
    }
    setIsExecuting(false);
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <WorkflowToolbar 
        onExecute={executeWorkflow} 
        isExecuting={isExecuting}
      />
      <div style={{ flex: 1, display: 'flex' }}>
        <NodePalette 
          templates={nodeTemplates} 
          style={{ width: '200px' }}
        />
        <div style={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
          >
            <Background />
            <Controls />
          </ReactFlow>
        </div>
        {selectedNode && (
          <NodeConfigPanel
            node={selectedNode}
            template={nodeTemplates.find(t => t.type === selectedNode.type)}
            onClose={() => setSelectedNode(null)}
            onUpdate={(updatedData) => {
              setNodes((nds) =>
                nds.map((n) => {
                  if (n.id === selectedNode.id) {
                    return { ...n, data: { ...n.data, ...updatedData } };
                  }
                  return n;
                })
              );
            }}
          />
        )}
      </div>
    </div>
  );
}

export default App; 
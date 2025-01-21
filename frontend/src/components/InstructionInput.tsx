import React, { useState } from 'react';

interface InstructionInputProps {
  onSubmit: (instruction: string) => void;
  isProcessing: boolean;
}

function InstructionInput({ onSubmit, isProcessing }: InstructionInputProps) {
  const [instruction, setInstruction] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (instruction.trim() && !isProcessing) {
      onSubmit(instruction);
      setInstruction('');
    }
  };

  return (
    <div style={{
      padding: '20px',
      borderTop: '1px solid #ccc',
      backgroundColor: '#f5f5f5',
    }}>
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="输入指令，例如：'生成一份关于人工智能在金融领域应用的5000字中文报告'"
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: '4px',
              border: '1px solid #ccc',
              minHeight: '60px',
              resize: 'vertical',
            }}
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={isProcessing || !instruction.trim()}
            style={{
              padding: '10px 20px',
              backgroundColor: isProcessing ? '#ccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              height: 'fit-content',
            }}
          >
            {isProcessing ? '处理中...' : '执行'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default InstructionInput; 
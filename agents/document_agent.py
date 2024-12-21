import os 
from core.base_agent import BaseAgent
from core.llm_provider import OpenAIProvider

class DocumentAgent(BaseAgent):
    def __init__(self, output_dir="output_docs"):
        self.output_dir = output_dir
        self.llm_provider = OpenAIProvider()
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def handle_task(self, task):
        if task.task_type != "create_document":
            return f"Unsupported task type: {task.task_type}"

        # 获取文件名和文档类型
        filename = task.kwargs.get("filename", "untitled_document.txt")
        doc_type = task.kwargs.get("doc_type", "general")
        
        # 构建提示词
        prompt = f"""Please create a {doc_type} document based on the following requirements:
        
        {task.prompt}
        
        Please provide the content directly without any additional formatting or explanations."""

        # 使用LLM生成内容
        content = self.llm_provider.generate_response(prompt)
        
        file_path = os.path.join(self.output_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Document created successfully: {file_path}"
        except Exception as e:
            return f"Error creating document: {e}"


from core.task_definition import Task
from agents.document_agent import DocumentAgent

def main():
    # 创建文档agent
    doc_agent = DocumentAgent()
    
    # 创建任务
    task = Task(
        task_type="create_document",
        prompt="Analyze the current state of artificial intelligence in finance, including its applications in trading, risk management, and personal banking. Discuss both benefits and potential risks.",
        kwargs={
            "filename": "ai_in_finance_5000.docx",
            "doc_type": "analytical report",
            "word_count": 5000
        }
    )
    
    # 执行任务
    result = doc_agent.handle_task(task)
    print(result)

if __name__ == "__main__":
    main() 
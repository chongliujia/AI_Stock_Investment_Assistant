from core.task_definition import Task
from agents.document_agent import DocumentAgent

def main():
    # 创建文档agent
    doc_agent = DocumentAgent()
    
    # 创建英文文档任务
    en_task = Task(
        task_type="create_document",
        prompt="Analyze the current state of artificial intelligence in finance, including its applications in trading, risk management, and personal banking. Discuss both benefits and potential risks.",
        kwargs={
            "doc_type": "analytical_report",
            "word_count": 1000,
            "lang": "en"
        }
    )
    
    # 创建中文文档任务
    zh_task = Task(
        task_type="create_document",
        prompt="分析人工智能在现代金融领域的应用现状，包括在交易、风险管理和个人银行业务中的应用。讨论其带来的优势和潜在风险。",
        kwargs={
            "doc_type": "分析报告",
            "word_count": 1000,
            "lang": "zh"
        }
    )
    
    # 执行任务
    print("Generating English document...")
    en_result = doc_agent.handle_task(en_task)
    print(en_result)
    
    print("\nGenerating Chinese document...")
    zh_result = doc_agent.handle_task(zh_task)
    print(zh_result)

if __name__ == "__main__":
    main() 
from core.task_definition import Task
from agents.document_agent import DocumentAgent

def main():
    # 创建文档agent
    doc_agent = DocumentAgent()
    
    # 创建任务
    task = Task(
        task_type="create_document",
        prompt="Write a short blog post about artificial intelligence and its impact on society.",
        filename="ai_blog_post.txt",
        doc_type="blog post"
    )
    
    # 执行任务
    result = doc_agent.handle_task(task)
    print(result)

if __name__ == "__main__":
    main()

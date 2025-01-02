from core.task_definition import Task
from agents.document_agent import DocumentAgent

def main():
    # 创建文档agent
    doc_agent = DocumentAgent()
    
    # 创建中文文档任务
    task = Task(
        task_type="create_document",
        prompt="""分析人工智能在现代金融领域的应用现状及未来趋势，请详细涵盖以下方面：

1. 当前金融领域AI应用的主要场景：
   - 智能交易和投资决策
   - 风险评估和管理
   - 个人银行业务和客户服务
   - 反欺诈和安全防护

2. 技术实现和解决方案：
   - 机器学习算法在金融领域的应用
   - 深度学习在市场分析中的作用
   - 自然语言处理在金融服务中的应用
   - 计算机视觉技术在支付验证中的使用

3. 实际案例分析：
   - 国内外领先金融机构的AI应用案例
   - 创新金融科技公司的技术突破
   - 具体项目实施效果和收益分析

4. 面临的挑战和解决方案：
   - 技术实现难点
   - 数据安全和隐私保护
   - 监管合规要求
   - 人才和成本问题

5. 未来发展趋势和机遇：
   - 新技术融合（区块链、物联网等）
   - 创新应用场景
   - 产业变革影响
   - 投资机会分析

请提供详实的数据支持和具体案例分析，确保内容的专业性和参考价值。""",
        kwargs={
            "doc_type": "行业研究报告",
            "word_count": 5000,
            "lang": "zh"
        }
    )
    
    # 执行任务
    result = doc_agent.handle_task(task)
    print(result)

if __name__ == "__main__":
    main() 
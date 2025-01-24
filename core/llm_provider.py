import os
import time
from openai import OpenAI
from openai import APIError, RateLimitError
from typing import Optional
from dotenv import load_dotenv
import logging
import httpx

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self, model: Optional[str] = None):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = model  # 保存传入的模型名称
        self.default_model = 'gpt-4-turbo-preview'  # 默认模型
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.timeout = int(os.getenv('TIMEOUT', 300))
        
        if not self.api_key:
            raise ValueError("API key not found in environment variables")
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.openai.com/v1"  # 使用默认的API端点
        )

    def generate_response(self, prompt: str, attempt: int = 1) -> Optional[str]:
        """生成回复"""
        try:
            logger.info(f"Attempting to generate response with model {self.model or self.default_model} (attempt {attempt})")
            
            response = self.client.chat.completions.create(
                model=self.model or self.default_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content.strip()
                
        except RateLimitError:
            wait_time = (2 ** attempt) + 1  # 指数退避
            logger.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
                
        except APIError as e:
            logger.error(f"API Error: {str(e)}")
            if "model_not_found" in str(e):
                # 如果模型不可用，尝试回退到GPT-3.5
                if self.model != "gpt-3.5-turbo":
                    logger.info("Falling back to GPT-3.5-turbo")
                    self.model = "gpt-3.5-turbo"
                    return self.generate_response(prompt, attempt)
            raise
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            if attempt == self.max_retries - 1:
                raise
                
        return None

    def generate_response_sync(self, prompt: str, max_attempts: int = 3) -> str:
        """同步方式生成响应"""
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的AI助手，擅长分析和生成高质量内容。"},
                {"role": "user", "content": prompt}
            ]
            
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Attempting to generate response with model {self.model or self.default_model} (attempt {attempt + 1})")
                    
                    response = self.client.chat.completions.create(
                        model=self.model or self.default_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    logger.info(f"Response generated successfully")
                    return response.choices[0].message.content
                    
                except RateLimitError:
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    
                except APIError as e:
                    if attempt < max_attempts - 1:
                        logger.warning(f"API Error: {str(e)}")
                        time.sleep(2)
                    else:
                        raise
                        
                except Exception as e:
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        time.sleep(2)
                    else:
                        raise
                        
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return "无法生成响应"

    def get_available_models(self) -> dict:
        """获取可用的模型列表"""
        return {
            "gpt-4-turbo-preview": "GPT-4 Turbo",
            "gpt-4": "GPT-4",
            "gpt-3.5-turbo": "GPT-3.5 Turbo",
        } 
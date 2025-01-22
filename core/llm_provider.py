import os
import time
from openai import OpenAI
from openai import APIError, RateLimitError
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.default_model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.timeout = int(os.getenv('TIMEOUT', 300))
        
        if not self.api_key:
            raise ValueError("API key not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # 设置代理
        if os.getenv('HTTPS_PROXY'):
            self.client.proxy = os.getenv('HTTPS_PROXY')

    def generate_response(self, prompt: str, model: Optional[str] = None, 
                         temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        生成LLM响应，包含重试和错误处理机制
        """
        model = model or self.default_model
        attempt = 0
        
        while attempt < self.max_retries:
            try:
                logger.info(f"Attempting to generate response with model {model} (attempt {attempt + 1})")
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的AI助手，擅长分析和生成高质量内容。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                duration = time.time() - start_time
                logger.info(f"Response generated successfully in {duration:.2f} seconds")
                
                return response.choices[0].message.content.strip()
                
            except RateLimitError:
                wait_time = (2 ** attempt) + 1  # 指数退避
                logger.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
            except APIError as e:
                logger.error(f"API Error: {str(e)}")
                if "model_not_found" in str(e):
                    # 如果模型不可用，尝试回退到GPT-3.5
                    if model != "gpt-3.5-turbo":
                        logger.info("Falling back to GPT-3.5-turbo")
                        model = "gpt-3.5-turbo"
                        continue
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                
            attempt += 1
            
        raise Exception(f"Failed to generate response after {self.max_retries} attempts")

    def generate_response_sync(self, prompt: str, max_attempts: int = 3) -> str:
        """同步方式生成响应"""
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的AI助手，擅长分析和生成高质量内容。"},
                {"role": "user", "content": prompt}
            ]
            
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Attempting to generate response with model {self.default_model} (attempt {attempt + 1})")
                    
                    response = self.client.chat.completions.create(
                        model=self.default_model,
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
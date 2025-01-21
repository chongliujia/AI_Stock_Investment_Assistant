import os
import json
import logging
from openai import OpenAI
from openai import APIError, RateLimitError

logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self, api_key=None, proxy=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        self.client = OpenAI(
            api_key=self.api_key,
            http_client=proxy
        )
        
    def generate_response(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=None):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise
            
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {str(e)}")
            raise 
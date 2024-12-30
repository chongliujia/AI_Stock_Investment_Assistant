import os
import openai
from dotenv import load_dotenv

class OpenAIProvider:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')

    def generate_response(self, prompt):
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content writer and researcher. Please respond in the same language as the prompt. Create well-structured, comprehensive documents with clear sections and detailed content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=8000,
                presence_penalty=0.6,
                frequency_penalty=0.6,
                top_p=0.9
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}" 
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")
        

        genai.configure(api_key=api_key)
        self.model = self._get_available_model()
    
    def _get_available_model(self):
        """Try to get an available free model"""

        free_models = [
            'gemini-1.5-flash',
        ]
        
        for model_name in free_models:
            try:
                model = genai.GenerativeModel(model_name)
                test_response = model.generate_content("Say 'test'")
                if test_response and test_response.text:
                    logger.info(f"Successfully initialized Gemini model: {model_name}")
                    return model
            except Exception as e:
                logger.debug(f"Model {model_name} not available: {e}")
                continue
    
        try:
            available_models = genai.list_models()
            logger.error("Available models:")
            for model in available_models:
                if hasattr(model, 'name'):
                    logger.error(f"- {model.name}")
                    if 'generateContent' in getattr(model, 'supported_generation_methods', []):
                        try:
                            return genai.GenerativeModel(model.name)
                        except:
                            continue
        except Exception as e:
            logger.error(f"Could not list available models: {e}")
        raise Exception("No available Gemini models found. Please check your API key and try again.")
    
    def generate_article(self, keyword, blog_categories=None):
        """
        Generate an article title and content using Gemini API
        
        Args:
            keyword (str): The keyword/topic for the article
            blog_categories (list): Optional blog categories for context
        
        Returns:
            dict: Contains 'title', 'content', 'success', and 'error' keys
        """
        try:
            categories_context = ""
            if blog_categories and len(blog_categories) > 0:
                categories_context = f" The blog focuses on categories like: {', '.join(blog_categories)}."
            
            prompt = f"""
            Write a professional blog article about "{keyword}".{categories_context}
            
            Requirements:
            1. Create an engaging title
            2. Write 3-5 well-structured sentences that provide valuable, informative content about the topic
            3. Make the content professional, engaging, and suitable for a blog audience
            
            Please format your response exactly like this:
            Title: Your engaging title here
            Content: Your informative content here (3-5 sentences)
            
            Do not include any additional text, explanations, or formatting.
            """
   
            response = self.model.generate_content(prompt)
      
            if not response or not response.text:
                return {
                    'success': False,
                    'title': '',
                    'content': '',
                    'error': 'No content was generated. Please try again with a different keyword.'
                }
            
            generated_text = response.text.strip()
            
            title = ""
            content = ""
            
            lines = generated_text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line.lower().startswith("title:"):
                    title = line[6:].strip() 
                elif line.lower().startswith("content:"):
                    content = line[8:].strip() 
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if next_line and not next_line.lower().startswith(('title:', 'content:')):
                            content += " " + next_line
                        else:
                            break
                    break
            
            if not title or not content:
                parts = generated_text.split('\n\n')
                if len(parts) >= 2:
                    first_part = parts[0].strip()
                    second_part = parts[1].strip()
                    
                    if first_part.lower().startswith("title:"):
                        title = first_part[6:].strip()
                    else:
                        title = first_part
                    
                    if second_part.lower().startswith("content:"):
                        content = second_part[8:].strip()
                    else:
                        content = second_part
                
                elif len(generated_text.split('\n')) >= 2:
                    lines = generated_text.split('\n')
                    title_line = lines[0].strip()
                    content_lines = [line.strip() for line in lines[1:] if line.strip()]
                    
                    if title_line.lower().startswith("title:"):
                        title = title_line[6:].strip()
                    else:
                        title = title_line
                    
                    content = " ".join(content_lines)
                    if content.lower().startswith("content:"):
                        content = content[8:].strip()
            
            if not title or not content:
                sentences = generated_text.split('.')
                if len(sentences) > 1:
                    title = sentences[0].strip()
                    if not title.endswith('.'):
                        title += '.'
                    content = '. '.join([s.strip() for s in sentences[1:] if s.strip()])
                    if content and not content.endswith('.'):
                        content += '.'
                else:
                    title = f"Complete Guide to {keyword}"
                    content = generated_text
            
            title = title.strip().strip('"\'').strip('*').strip()
            content = content.strip().strip('"\'').strip('*').strip()
            if title.lower().startswith('title:'):
                title = title[6:].strip()
            if content.lower().startswith('content:'):
                content = content[8:].strip()
            
            if not title or len(title) < 5:
                title = f"The Ultimate Guide to {keyword}"
            
            if not content or len(content) < 20:
                content = f"This comprehensive article explores everything you need to know about {keyword}, providing valuable insights and practical information for readers interested in this topic."
            
            if content and not content.rstrip().endswith(('.', '!', '?')):
                content += '.'
            
            return {
                'success': True,
                'title': title,
                'content': content,
                'error': None
            }
            
        except Exception as e:
            error_message = str(e).lower()
            
            if 'quota exceeded' in error_message or 'rate limit' in error_message:
                logger.error("Gemini API rate limit exceeded")
                return {
                    'success': False,
                    'title': '',
                    'content': '',
                    'error': 'API rate limit exceeded. Please try again in a moment.'
                }
            elif 'api key' in error_message or 'authentication' in error_message:
                logger.error("Gemini API authentication failed")
                return {
                    'success': False,
                    'title': '',
                    'content': '',
                    'error': 'API authentication failed. Please check your Gemini API key in .env file.'
                }
            elif 'not found' in error_message or '404' in error_message:
                logger.error("Gemini model not found")
                return {
                    'success': False,
                    'title': '',
                    'content': '',
                    'error': 'AI model not available. Please try again later or contact support.'
                }
            elif 'blocked' in error_message or 'safety' in error_message:
                logger.error("Content was blocked by Gemini safety filters")
                return {
                    'success': False,
                    'title': '',
                    'content': '',
                    'error': 'Content was blocked by safety filters. Please try a different keyword.'
                }
            elif 'connection' in error_message or 'timeout' in error_message:
                logger.error("Gemini API connection error")
                return {
                    'success': False,
                    'title': '',
                    'content': '',
                    'error': 'Connection error. Please check your internet connection and try again.'
                }
            elif 'invalid argument' in error_message:
                logger.error("Invalid request to Gemini API")
                return {
                    'success': False,
                    'title': '',
                    'content': '',
                    'error': 'Invalid request. Please try a different keyword.'
                }
            else:
                logger.error(f"Unexpected error in Gemini service: {e}")
                return {
                    'success': False,
                    'title': '',
                    'content': '',
                    'error': f'An unexpected error occurred: {str(e)}'
                }
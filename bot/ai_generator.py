import os
import hashlib
import json
import requests
import time
from loguru import logger

class AIGenerator:
    def __init__(self):
        self.cache_dir = "cache"
        self.cache_enabled = os.getenv("CACHE_ENABLED", "true") == "true"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Статистика и мониторинг
        self.stats = {
            'total_requests': 0,
            'successful': 0,
            'errors': 0,
            'last_error': None,
            'last_success': None,
            'error_codes': {}
        }
    
    def _get_cache_path(self, content_hash):
        return os.path.join(self.cache_dir, f"{content_hash}.json")
    
    def _load_from_cache(self, content_hash):
        if not self.cache_enabled:
            return None
            
        cache_path = self._get_cache_path(content_hash)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)["content"]
            except Exception as e:
                logger.error(f"Cache read error: {str(e)}")
        return None
    
    def _save_to_cache(self, content_hash, content):
        if not self.cache_enabled:
            return
            
        cache_path = self._get_cache_path(content_hash)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"content": content}, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Cache write error: {str(e)}")
    
    def _log_error(self, error_type, status_code=None):
        self.stats['errors'] += 1
        self.stats['last_error'] = {
            'time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'type': error_type,
            'code': status_code
        }
        
        if status_code:
            if status_code not in self.stats['error_codes']:
                self.stats['error_codes'][status_code] = 0
            self.stats['error_codes'][status_code] += 1
    
    def get_status(self):
        """Возвращает текущий статус генератора"""
        return {
            'provider': 'deepseek',
            'stats': self.stats,
            'cache': {
                'enabled': self.cache_enabled,
                'size': len(os.listdir(self.cache_dir)) if os.path.exists(self.cache_dir) else 0
            }
        }
    
    def generate_content(self, title, description):
        self.stats['total_requests'] += 1
        content = f"{title}\n\n{description}"
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Проверка кэша
        cached = self._load_from_cache(content_hash)
        if cached:
            return cached
        
        try:
            result = self._generate_with_deepseek(title, description)
            self._save_to_cache(content_hash, result)
            self.stats['successful'] += 1
            self.stats['last_success'] = time.strftime("%Y-%m-%d %H:%M:%S")
            return result
        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            self._log_error("Generation Error")
            return content

    def _generate_with_deepseek(self, title, description):
        """Генерация контента через DeepSeek API"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        url = "https://api.deepseek.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты профессиональный журналист. Создай увлекательный пост для Telegram на основе новости. Сделай текст: 1. Живым и эмоциональным 2. С эмодзи 3. С разбивкой на абзацы 4. До 500 символов"
                },
                {
                    "role": "user",
                    "content": f"Заголовок: {title}\n\nТекст: {description}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # Обработка HTTP ошибок
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f": {error_data.get('error', {}).get('message', 'Unknown error')}"
                except:
                    pass
                
                self._log_error("HTTP Error", response.status_code)
                raise Exception(error_msg)
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        
        except requests.exceptions.Timeout:
            self._log_error("Timeout")
            raise Exception("API request timed out")
        
        except requests.exceptions.ConnectionError:
            self._log_error("Connection Error")
            raise Exception("Connection to API failed")
        
        except Exception as e:
            self._log_error("General Error")
            raise
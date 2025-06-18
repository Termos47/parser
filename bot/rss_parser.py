import feedparser
import requests
from bs4 import BeautifulSoup
from loguru import logger

class RSSParser:
    @staticmethod
    def parse_feed(url):
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                logger.warning(f"Empty feed: {url}")
                return []
                
            return feed.entries
        except Exception as e:
            logger.error(f"RSS parse error: {str(e)}")
            return []
    
    @staticmethod
    def clean_html(text):
        if not text:
            return ""
        return BeautifulSoup(text, "html.parser").get_text().strip()
    
    @staticmethod
    def extract_image(entry):
        # Поиск изображений в медиа-контенте
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('type', '').startswith('image'):
                    return media['url']
        
        # Поиск в enclosures
        if hasattr(entry, 'enclosures'):
            for enc in entry.enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.href
        
        # Поиск в контенте
        if hasattr(entry, 'content'):
            for content in entry.content:
                if hasattr(content, 'value'):
                    soup = BeautifulSoup(content.value, 'html.parser')
                    img = soup.find('img')
                    if img and img.get('src'):
                        return img['src']
        
        # Поиск в описании
        if hasattr(entry, 'description'):
            soup = BeautifulSoup(entry.description, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                return img['src']
        
        return None
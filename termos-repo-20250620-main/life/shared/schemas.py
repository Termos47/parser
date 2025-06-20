from pydantic import BaseModel

class NewsItem(BaseModel):
    title: str
    content: str
    source: str
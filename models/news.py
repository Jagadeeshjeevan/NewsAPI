from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NewsArticle(BaseModel):
    id: int
    title: str
    description: str
    content: str
    author: Optional[str] = None
    category: str
    image_url: Optional[str] = None
    source: str
    published_at: datetime
    url: str


class NewsResponse(BaseModel):
    status: str
    total: int
    articles: list[NewsArticle]

from abc import ABC, abstractmethod
from typing import List, Dict


class NewsItem:
    def __init__(self, title: str, url: str, description: str, source: str, 
                 category: str = None, tags: List[str] = None, 
                 date_published: str = None, author: str = None):
        self.title = title
        self.url = url
        self.description = description
        self.source = source
        self.category = category
        self.tags = tags or []
        self.date_published = date_published
        self.author = author
    
    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'source': self.source,
            'category': self.category,
            'tags': self.tags,
            'date_published': self.date_published,
            'author': self.author
        }


class DataSource(ABC):
    @abstractmethod
    def fetch(self) -> List[NewsItem]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        pass
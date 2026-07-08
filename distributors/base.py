from abc import ABC, abstractmethod
from typing import List, Dict


class Report:
    def __init__(self, content: str, date: str, news_count: int = 0):
        self.content = content
        self.date = date
        self.news_count = news_count
    
    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'date': self.date,
            'news_count': self.news_count
        }


class Distributor(ABC):
    @abstractmethod
    def distribute(self, report: Report) -> bool:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
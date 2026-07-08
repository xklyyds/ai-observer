from abc import ABC, abstractmethod
from typing import List
from data_sources.base import NewsItem


class Processor(ABC):
    @abstractmethod
    def process(self, news_items: List[NewsItem]) -> List[NewsItem]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
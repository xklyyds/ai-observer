from .base import Processor
from .categorizer import NewsCategorizer
from .summary import AISummarizer
from .trend_analyzer import TrendAnalyzer


PROCESSOR_REGISTRY = {
    "categorizer": NewsCategorizer,
    "summarizer": AISummarizer,
    "trend_analyzer": TrendAnalyzer,
}


def get_all_processors() -> list:
    return [
        NewsCategorizer(),
        AISummarizer(),
        TrendAnalyzer(),
    ]


def get_processor(name: str, **kwargs) -> Processor:
    if name in PROCESSOR_REGISTRY:
        return PROCESSOR_REGISTRY[name](**kwargs)
    raise ValueError(f"Unknown processor: {name}")